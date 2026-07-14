---
hide:
  - navigation
---

# ComAp InteliLite/AMF25 — Protocol Reverse-Engineering Notes

This document records everything established during the reverse-engineering session: the
UDP discovery protocol, the native ECDH/AES-encrypted TCP protocol InteliConfig actually
uses (port 23, *not* gRPC, *not* real Telnet despite the port number), and how Modbus fits
in. It is meant to be a complete enough reference to implement a Python client without
re-deriving any of this from scratch.

Everything here was derived from:

- Live Wireshark/tshark captures (both router-side `tcpdump` over SSH, and PC-side Wireshark
  next to InteliConfig).
- Decompiling ComAp's own `CommunicationServer` .NET assemblies with `ilspycmd` (ILSpy). The
  assemblies are **not obfuscated** — full class/method names survive decompilation.
- A working Python proof-of-concept client (see `comap_client.py`) that completed a full
  live handshake and authenticated read against a real controller at `192.168.1.9`.

## 0. The three channels

| Channel | Transport | Status | Use |
|---|---|---|---|
| UDP discovery | UDP 2413 | Reverse-engineered, unencrypted | Autodiscovery — used by the component's `config_flow` |
| Native protocol | TCP 23 | Reverse-engineered, ECDH+AES encrypted | **Primary data source for the component** — what InteliConfig itself uses |
| Modbus | TCP 502 (or RTU) | Vendor-documented, supported | Not currently used by the component; kept here as reference (see §3) and as a cross-reference for object IDs/names while decoding the native protocol's compound objects |

> The library and component build on UDP discovery + the native protocol only, for now.
> Modbus support is out of scope for the library; §3 below stays as a factual reference
> since `cfgmodbus.txt`'s `Com.Obj. #` column shares the same ID space as the native
> protocol's `CommunicationObject` IDs and may help decode the native protocol's
> still-unknown compound-object layouts.

## 1. UDP discovery protocol (port 2413)

- InteliConfig broadcasts a probe from a random ephemeral source port to
  `<subnet-broadcast>:2413` (e.g. `192.168.1.255:2413`) periodically while its main window is
  open (observed on app open/reopen).
- **The probe and reply are not a bespoke discovery-only format** — despite living on their
  own UDP port, they're a regular `EthernetMessage` (see §2.1 below for the full framing
  spec): a `SendMe` for a `Discovery` communication object (`0x5ead` = 24237), CRC16 and all.
  Confirmed straight from the decompiled `ComAp.Communication.Core` (`UdpDiscoveryManager`):
  ```csharp
  private static byte[] CreateDiscoveryMessage()
  {
      return new EthernetMessage(new Message.Parameters
      {
          MessageType = Message.Type.ClientToServer,
          MessageOperation = Message.Operation.SendMe,
          CommunicationObject = CommunicationObject.Discovery
      }, 0).Save();
  }
  ```
  i.e. `build_inner(Operation.SEND_ME, addr=1, comm_obj=0x5ead, data=b"", ident=0)` →
  `00 00 00 00 ad 5e fd 73` (the trailing `ad 5e fd 73` is **not** a random per-probe nonce —
  it's `comm_obj` (`ad 5e` LE = `0x5ead`) + the CRC16 of the rest (`fd 73` LE), constant for
  every valid probe regardless of who sends it). **The controller validates this CRC and
  silently drops anything that doesn't pass** — an early implementation that built the probe
  as 4 reserved bytes + 4 *random* bytes got ignored essentially every time (1/65536 chance of
  a random CRC match), while real InteliConfig traffic got a reply on every single probe. This
  was the actual root cause of an extended debugging session that initially (incorrectly)
  suspected client isolation / VLANs / switch storm-control — the probe simply wasn't a valid
  message.
- The controller replies **unicast**, from UDP port 2413 to the probe's source port, with
  another `EthernetMessage`: `SendTo`, same `Discovery` comm object, data = a binary
  `DiscoveryDevice` payload. The Wireshark hex of one real reply:
  ```
  IP 192.168.1.9 -> 192.168.1.181, UDP sport=2413 dport=<probe's ephemeral port>
  payload (73 bytes):
  41 00 01 00 ad 5e 01 04 00 00 00 00 c9 00 a1 0f
  c0 a8 01 09 68 69 f2 02 2e 86 17 00 01 00 00 00
  00 00 00 00 00 75 90 00 00 00 0f 00 01 00 00 00
  01 0e 46 56 20 31 35 30 30 30 00 00 00 00 00 00
  00 00 22 29 12 76 18 18
  ```
  Stripping the 6-byte `EthernetMessage` header + 2-byte trailing CRC leaves a 65-byte
  `DiscoveryDevice` payload, decoded field-by-field from the decompiled `DiscoveryDevice.Load`
  (`ComAp.Communication.Core`):

  | offset | size | field | example value |
  |---|---|---|---|
  | 0 | 1 | `FormatVersion` | `1` |
  | 1 | 1 | `Type` (`DeviceType` enum: `IbNt=0, IbCom=1, IbLite=2, CmEthernet=4, IG500BuiltInEthernet=5`) | `4` (`CmEthernet`) |
  | 2 | 4 | `SerialNumber` (uint32 LE) | `0` |
  | 6 | 2 | firmware major/minor (uint16 LE) | `201` |
  | 8 | 2 | firmware patch/build (uint16 LE) — only present when `FormatVersion >= 1`; header is 42 bytes total for version 0, 44 for version 1+ | `4001` |
  | 10 | 4 | `IPAddress` (4 raw bytes, in order) | `c0 a8 01 09` = `192.168.1.9` |
  | 14 | 6 | `MACAddress` (6 raw bytes) | `68:69:f2:02:2e:86` |
  | 20 | 2 | `CommunicationPort` (uint16 LE) — the TCP port for §2's protocol | `23` |
  | 22 | 1 | `SelectedAccessType` (flags: `IpAddress=1, AirGate=2`) | `1` |
  | 23 | 16 | `AirgateIdentifier` (ASCII, null-terminated) | `""` |
  | 39 | 4 | `ConnectedUnits` (bitmask, one bit per unit address) | `0b1` |
  | 43 | 1 | `IsUnitsListComplete` (0/1) | `1` |
  | 44 | 21×N | one `DiscoveryUnit` record per remaining 21 bytes (see below) | 1 unit |

  Each 21-byte `DiscoveryUnit` record: `Type` (1 byte) + `Name` (16 bytes ASCII,
  null-terminated) + `SerialNumber` (4 raw bytes, displayed as hex — *not* a little-endian
  uint32; reading the bytes in stream order and hex-encoding them directly reproduces the
  serial number shown in InteliConfig's UI exactly, e.g. `22 29 12 76` → `"22291276"`).
  Decoding the real reply above gives `ip=192.168.1.9`, `mac=68:69:f2:02:2e:86`,
  `comm_port=23`, one unit `name="FV 15000"` `serial="22291276"` — matching InteliConfig's own
  discovered-device card exactly (IP and SN both visible there).
- **Caveat (router hardware-switch blind spot):** if you try to capture this on a router with
  a hardware-offloaded switch (DSA-style, seen `switch0` and per-port `ethN@switch0`
  interfaces in `ip link`), unicast traffic between two LAN hosts on the same VLAN may be
  switched entirely in silicon and never reach the CPU's Linux bridge netdev — `tcpdump -i
  br0` will see the broadcast probe but **not** the unicast reply. Broadcasts get flooded to
  the CPU so they're always visible; unicast reads need to be captured on one of the actual
  endpoints (or via port mirroring/SPAN if the switch supports it).

## 2. Native protocol (TCP port 23) — "EthernetMessage" protocol

This is what `ComAp.Communication.Service.exe` (a separate background Windows service,
*not* InteliConfig.exe itself) speaks to the controller. InteliConfig.exe talks to that local
service over **gRPC on localhost** (see service logs:
`/Server.ControllerReadDataContract/GetCommunicationObjectsValues` etc.) — the gRPC layer
never touches the network to the controller, it's purely local IPC. The actual wire protocol
to the controller is this custom binary protocol, exposed over plain TCP on port 23.
Wireshark labels it "TELNET" purely because of the port number; the bytes are not telnet.

### 2.1 Wire framing — two nested layers

**Layer 1 (outer "block alignment" wrapper).** Present on every message **except** the very
first one (see §2.4 step 2):
```
[1 byte: block_count][block_count * 16 bytes: payload, zero-padded to the block boundary]
```
- Before AES is established this payload is the literal inner message, unencrypted
  (`NoCipherAligned` in the decompiled source).
- After AES is established (§2.4 step 9 onward) this payload is AES-256-CBC ciphertext of
  the inner message (§2.3).

**Layer 2 (inner "EthernetMessage"):**
```
offset  size  field
0       2     data_length : uint16 LE — length of `data` below (header/CRC not included)
2       1     bit-packed: bits[0:3] = Operation (§2.2), bits[3:8] = ControllerAddress - 1
3       1     Identifier — sequence/correlation byte
4       2     CommunicationObject ID : uint16 LE
6       dlen  data
6+dlen  2     CRC16 LE, computed over bytes [0 .. 6+dlen) — i.e. header+data, NOT itself
```
Total inner message length = `data_length + 8`.

**Exception — the very first message of any connection.** The controller proactively pushes
`VersionIB` the instant the TCP connection opens, using the plain `EthernetMessage` layout
directly with **no outer block-wrapper** (cipher is `NoCipher`, a pure passthrough, at this
point). Every message from then on — both directions — goes through the outer wrapper.

**`SendToBlock` (op=2) messages** insert one extra byte right after the 6-byte header:
```
offset 6:    block_info byte — bits[0:7] = block_index, bit[7] = is_last_block
offset 7..:  data (length = data_length - 1)
```
Used for objects too large for one message (e.g. `ValuesAll`/`ConfigurationTable` may or may
not need this depending on size vs. negotiated max length, see §2.4 step 12). After receiving
a non-final block, the client must send `Next` (op=3) with no data to request the following
block.

### 2.2 CRC16

Standard MODBUS/ANSI CRC16 — init `0xFFFF`, polynomial `0xA001` (reflected `0x8005`), no
final XOR. Verified byte-for-byte against multiple live captures and live traffic.

```python
def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc
```

### 2.3 Operation enum

```
SendMe        = 0   # client request: "send me object X" — no data
SendTo        = 1   # carries data — write request, or read response
SendToBlock   = 2   # one block of a large object, see block_info byte above
Next          = 3   # also "Acknowledgment" — request next block / ack a write
Error         = 4   # data = uint32 LE error code, see §2.6
Repeat        = 5
```

### 2.4 Full connection / handshake sequence

1. TCP connect to `<controller_ip>:23`.
2. Controller immediately sends `VersionIB` (CommunicationObject **24533**), op=`SendTo`,
   2-byte data, **plain framing** (no outer wrapper, no encryption) — this is the one
   exception described in §2.1.
   - `data` as `uint16` LE: bits `0..15` (mask `0x7FFF`) = protocol version. Bit `15`
     (`0x8000`) set ⇒ AES ciphering; clear ⇒ legacy Blowfish (`BlowfishCipher` — present in
     the decompiled source but not implemented in our PoC client; assume modern firmware
     uses AES).
3. Switch local framing mode to "block-wrapped" — every message from here on (both
   directions) is `[1-byte count][count*16 bytes]`.
4. Client sends `SendMe(EcdhPublicKey)` — CommunicationObject **24119**, no data.
5. Controller responds `SendTo(EcdhPublicKey)` with `data` = `[4 bytes unknown/reserved
   prefix][65-byte raw uncompressed EC point]` — curve is **secp256r1 (P-256)**, point format
   `0x04 || X[32] || Y[32]`. The decompiled `TerminalAesCipher` constructor does
   `controllerPublicKey.Skip(4)` to extract the point — i.e. **read = skip first 4 bytes**.
6. Client generates its own ephemeral EC keypair on secp256r1, and writes its public key
   back: `SendTo(EcdhPublicKey)` with `data` = `[1-byte length=65][65-byte raw uncompressed
   point]`. **This is asymmetric with step 5** — the write format is a 1-byte length prefix,
   not whatever 4-byte prefix the controller used on read. (Source: `TerminalAesCipher`
   constructor builds `PublicKey = [length_byte] + raw_point_bytes`.) Sending plain 65 raw
   bytes here fails with `BadWriteValue` (134217955) — confirmed live.
   - Controller acknowledges with `Next` (op=3), no data.
7. Compute the ECDH shared secret: X-coordinate of `our_private_key * their_public_key` on
   secp256r1, as 32 bytes big-endian (left-zero-padded if the X-coordinate is short — BouncyCastle
   does `AddLeadingZero(.., 32)`; Python's `cryptography` `exchange()` already returns 32
   bytes for P-256 so this is automatic).
8. Derive the AES key and IV from the access code (the controller's numeric password, e.g.
   `"0"`), via **double HMAC-SHA256** keyed by the access code:
   ```python
   access_bytes = access_code.encode("utf-8")
   aes_key = hmac.new(access_bytes, shared_secret, hashlib.sha256).digest()        # 32 bytes -> AES-256 key
   iv      = hmac.new(access_bytes, aes_key,       hashlib.sha256).digest()[:16]   # 16 bytes
   ```
9. From here on, the outer block-wrapper's payload is **AES-256-CBC ciphertext** of the inner
   `EthernetMessage` (zero-padded to a 16-byte boundary before encryption — `PaddingMode.Zeros`
   on the .NET side, no real PKCS padding; just truncate after decrypting using the inner
   message's own `data_length` field).
   - **Critical/non-obvious:** there is exactly **one** IV value for the whole connection,
     shared between encryption and decryption, updated after *every single* AES operation —
     in *either* direction — to that operation's **ciphertext's** last 16 bytes. It is *not*
     two independent per-direction chains. Both peers stay in lock-step because the
     ciphertext bytes that drive the update are visible to both sides, in the same order,
     since this is a strict request/response protocol over one TCP connection. (Initially
     implementing this as two separate per-direction IV chains produces a connection that
     completes the handshake but then fails to decrypt anything, with CRC errors on every
     subsequent message — this was hit and fixed during the PoC.)
10. Verify access — **try the hash-challenge method first**:
    - `SendMe(VerifyAccessHash)` (CommunicationObject **24324**).
    - If the controller answers `Error` with code `TerminalAccessDisabled` (**134217960**) or
      `NonExistingCommunicationObject` (**100794368**) — expected on at least this firmware —
      fall back to step 11.
    - Otherwise the read succeeds and returns a nonce; compute
      `credentials = ascii(uppercase_hex(md5(nonce + ascii(access_code))))` (32 ASCII bytes —
      MD5 digest rendered as an uppercase hex string, then that *string* is what's sent, not
      the raw digest) and write it back via `SendTo(VerifyAccessHash)`.
11. **Fallback — plain access code** (this is the path our real controller actually uses):
    `SendTo(VerifyAccess)` (CommunicationObject **24534**) with `data` =
    `ascii(access_code)` null-padded to 16 bytes. Controller acknowledges with `Next`. This
    completed successfully against the real controller using access code `"0"`.
12. Read `MaxMessageDataLengths` (CommunicationObject **24269**) to learn the negotiated
    max per-message data sizes. Observed live response: `02 68 05 68 05 00 00` (7 bytes) —
    format byte `0x02` ⇒ `ServerToClient = uint16_le(bytes[1:3])`,
    `ClientToServer = uint16_le(bytes[3:5])` ⇒ both `0x0568` = **1384 bytes**.
13. Connection is now fully authenticated. Any `CommunicationObject` (§2.5) can be read or
    written with `SendMe`/`SendTo`, transparently handling `SendToBlock` continuation for
    large objects.

This entire sequence (steps 1–13) was executed live against a real InteliLite/AMF25
controller and succeeded, including reading `ValuesAll` (855 bytes) afterward and finding
the controller's own IP/MAC/netmask as readable ASCII substrings inside it — independent
confirmation the whole chain (framing, CRC, ECDH, AES, IV chaining, access verification) is
correct.

### 2.4.1 Writing password-protected setpoints

The **AccessCode** (steps 8-11) and the **Password** (for setpoint writes) are entirely
separate credentials:

- **AccessCode** (string, e.g. `"0"`) — gates the TCP connection itself; baked into the
  AES key via double HMAC-SHA256 (step 8). Factory default is `"0"`. Verified once per
  connection via `VerifyAccess`/`VerifyAccessHash`.
- **Password** (integer 0-9999) — gates individual setpoint writes based on each
  setpoint's configured `accessLevel` field. Factory default is also `0` (disabled). Stored
  independently of the AccessCode; changing one doesn't change the other.

To write a password-protected setpoint (one where a plain `write_object` returns
`ControllerError.INVALID_PASSWORD` = 134217978), submit the password via
`CommunicationObject.PASSWORD_FOR_WRITE` (24524, 2 bytes LE) over the already-established
AES channel, then perform the setpoint write:

```python
await client.authenticate("0")          # AccessCode — derives the AES key
await client.elevate_access(1234)       # Password  — CommunicationObject 24524
await client.write_object(number, raw)  # setpoint write now succeeds
```

`elevate_access(password: int)` is idempotent within a session — call it once before a
batch of writes rather than once per write. There is also a nonce-based hash variant
(`CommunicationObject.PASSWORD_FOR_WRITE_HASH` = 24286, 32 bytes) for controllers that
disable the plain submission, mirroring the `VerifyAccessHash`/`VerifyAccess` pattern from
steps 10-11 — not yet tested.

**Brute-force protection** (per the InteliLite Global Guide §5.3.4): 5 wrong attempts →
1 min lockout, doubling each time, 100 wrong → permanent lockout requiring a reset
procedure. Do not call `elevate_access` in a retry loop.

**Equivalent mechanisms on other channels** (all confirmed live):

| Channel | Password submission | Setpoint write |
|---|---|---|
| Native protocol (TCP/23) | `write_object(24524, uint16_le(password))` | `write_object(number, bytes)` |
| Modbus TCP (TCP/502) | Write `password` to reserved register 4211 (uint16 BE) | Write to setpoint's register address |
| Web UI (HTTP/80) | POST `MD5(page_nonce + str(password)).upper()` to `CONTROL.HTM` | Edit via `params.htm` |

The Modbus register 4211 is documented as a "reserved register" in the firmware's Modbus
table, not in the standard setpoint/value cfgmodbus export.

### 2.5 Known `CommunicationObject` IDs

Source: decompiled `ComAp.Controller.dll`, class `CommunicationObject` (a plain class with a
huge list of `public static readonly CommunicationObject Foo = new CommunicationObject(id,
size[, AccessType])` initializers — not a C# `enum`, which is why grepping for "enum
CommunicationObject" doesn't find it).

| Name | ID (dec) | ID (hex) | Size | Access | Notes |
|---|---|---|---|---|---|
| VersionIB | 24533 | 0x5FD5 | 2 | Read | sent unsolicited on connect |
| EcdhPublicKey | 24119 | 0x5E37 | variable | — | see §2.4 steps 4-6 for read/write asymmetry |
| VerifyAccessHash | 24324 | 0x5F04 | 32 | — | hash-challenge auth; disabled on our firmware |
| VerifyAccess | 24534 | 0x5FD6 | 16 | Write | plain-password auth fallback; **confirmed working** |
| MaxMessageDataLengths | 24269 | 0x5ECD | 5 | — | confirmed working |
| ComapProtocolFeatures | 24023 | 0x5DD7 | — | Read | used to pick CryptoSuite1 vs 2 |
| ValuesAll | 24560 | 0x5FF0 | variable | Read | **confirmed working live**, 855 bytes incl. IP/MAC |
| ValueStatesAll | 24555 | 0x5FEB | variable | Read | |
| ValueStatesAndDataAll | 24529 | 0x5FD1 | variable | Read | |
| ValuesCategoryI/II/III | 24563/24562/24561 | | variable | Read | |
| ValueStatesCategoryI/II/III | 24558/24557/24556 | | variable | Read | |
| SetpointsAll | 24559 | 0x5FEF | — | — | |
| SetpointsR | 24543 | 0x5FDF | variable | Read | |
| SetpointsP | 24544 | 0x5FE0 | variable | Read | |
| AlarmList | 24545 | 0x5FE1 | variable | Read | |
| AlarmListWithVersion | 24024 | 0x5DD8 | — | Read | |
| ConfigurationTable | 24575 | 0x5FFF | variable | Read | |
| TerminalConfigurationTable | 24574 | 0x5FFE | variable | Read | |
| ConfigurationTableCrc16 | 24573 | 0x5FFD | variable | Read | |
| TerminalConfigurationTableCrc16 | 24572 | 0x5FFC | 2 | Read | |
| SerialNumber | 24548 | 0x5FE4 | 4 | Read | |
| FirmwareVersionText | 24339 | 0x5F13 | 16 | Read | |
| BootloaderFirmwareVersion | 24277 | 0x5ED5 | 4 | Read | |
| ControllerFirmwareIdentification | 24115 | 0x5E33 | 1 | Read | |
| Command | 24551 | 0x5FE7 | 2 | Write | |
| CommandWithArgument | 23859 | 0x5D33 | — | — | |
| CommandArgument | 24550 | 0x5FE6 | 4 | — | |
| HistoryLength | 24538 | 0x5FDA | 2 | Read | |
| MaxHistoryRecords | 24564 | 0x5FF4 | 2 | Read | |
| ReadIndexInHistory | 24565 | 0x5FF5 | 2 | — | |
| WriteIndexInHistory | 24566 | 0x5FF6 | 2 | Read | |
| OlderHistoryRecord / YoungerHistoryRecord / YoungestHistoryRecord / NewHistoryRecords | 24567 / 24568 / 24569 / 24570 | | variable | Read | |
| CommunicationState | 24571 | 0x5FFB | 4 | Read | |
| ControllerAddress | 24537 | 0x5FD9 | 1 | — | |
| DisplayContrast | 24547 | 0x5FE3 | 1 | — | |
| GsmPin | 24536 | 0x5FD8 | 2 | Write | |
| ChangeAccess | 24535 | 0x5FD7 | — | Write | |
| SystemTime / Date / Time | 24552 / 24553 / 24554 | | 0/3/3 | — | |
| InteliMains | 24528 | 0x5FD0 | 4 | Write | |

This is a partial list (the full class has well over a hundred entries — most relate to
modem/GSM/history/programming features unlikely to be relevant to this project). To extend
this table, decompile `ComAp.Controller.dll` again and grep the `CommunicationObject` class
body (around line 31248 onward in our decompile) for the object you need.

### 2.6 Error codes

Source: decompiled `ComAp.GlobalShared.dll`, `public enum ControllerError : uint`.

| Name | Value (dec) | Value (hex) |
|---|---|---|
| Ok / None | 0 | 0x0 |
| NoAnswer | 1 | 0x1 |
| AnswerPostponed | 2 | 0x2 |
| NonExistingCommunicationObject | 100794368 | 0x06020000 |
| TerminalAccessDisabled | 134217960 | 0x080000E8 |
| BadWriteValue | 134217955 | 0x080000E3 |

(Full enum has many more members — re-decompile `ComAp.GlobalShared.dll` and grep `enum
ControllerError` to extend as needed. Error message data on the wire is the numeric value as
`uint32` LE.)

### 2.7 Forward secrecy — old captures cannot be decrypted

Because the ECDH keypairs are **ephemeral** (generated fresh per connection; the private key
never touches the wire), no previously captured session can ever be decrypted, no matter how
well this protocol is understood — there is a hard cryptographic wall, not a parsing gap.
Any future debugging of this protocol must be done **live** (a live client or a live MITM),
not from old `.pcap` files.

### 2.8 Source DLLs

All found under `C:\Program Files (x86)\ComAp PC Suite\Tools\CommunicationServer\` on a
machine with InteliConfig installed. Decompiled with `ilspycmd` (the cross-platform ILSpy
CLI, installed via `dotnet tool install ilspycmd`).

| DLL | Relevant contents |
|---|---|
| `ComAp.Communication.Core.dll` | `EthernetConnection`, `MessageManager`, `Message`/`EthernetMessage`/`AirgateMessage`, `Ciphering.AesCipher`/`TerminalAesCipher`/`BlowfishCipher`/`NoCipherAligned`, `CryptoSuite1`/`CryptoSuite2` |
| `ComAp.Common.dll` | `Crc16Bit`, `Crc8Bit` |
| `ComAp.Controller.dll` | `CommunicationObject` (all IDs), `Security.GetHashedCredentials` |
| `ComAp.GlobalShared.dll` | `ControllerError` enum |
| `BouncyCastle.Crypto.dll` | the EC/ECDH math library used .NET-side (confirms secp256r1 + raw `IBasicAgreement` ECDH, no KDF beyond what's in §2.4 step 8) |

This entire sequence is implemented in `pycomap.protocol.ComApClient` and validated live
against real hardware.

## 3. Modbus (existing, documented — reference only, not currently used by the component)

`cfgmodbus.txt` is exported directly from InteliConfig's own Modbus-configuration export
feature (not reverse-engineered — this is a supported, documented vendor feature). It's a
fixed-width text export with three tables:

| Table | Allowed Modbus functions | Content |
|---|---|---|
| `Binaries` | 01, 02 | Discrete inputs/coils — binary I/O, individual alarm bits, etc. |
| `Values` | 03, 04 | Holding/input registers — analog measurements, states, lists |
| `Setpoints` | 03, 04, 06, 16 | Holding registers, read/write — configuration values |

Common columns across tables (column layout differs slightly per table — see the file's own
`HEADER` block at the top for exact field widths):
- **Modbus address** (per-table addressing, e.g. `01000` for the first Values register)
- **Com.Obj. # ("C.O.#")** — this is literally the same `CommunicationObject` ID space as
  §2.5! E.g. `RPM` is C.O. `10123`, `ECU State` is C.O. `10034`. This means the Modbus table
  and the native protocol's object IDs are two views onto the *same* underlying controller
  object model — worth keeping in mind if cross-referencing or validating one against the
  other later.
- **Name**, **Dimension** (unit), **Type** (`Integer`/`Unsigned`/`Binary#N`/`List#N`/`String`/etc.),
  **Len** (register count), **Dec** (decimal places for scaling), **Min/Max**, **Group /
  Subgroup** (used for organizing entities)
- `Binaries` additionally has **Bit #** / **Bit Name** for individual bits within a binary
  word, and a `State`-row format (`Value`/`State` column) describing protection levels per
  bit (Level 1/Level 2/Sensor failure).

The component doesn't use Modbus as a transport for now (see §0), but this file's `Com.Obj. #`
column is still useful: it shares the same `CommunicationObject` ID space as the native
protocol (§2.5), so it can help map a known, human-readable, unit-and-type-annotated name
onto an object ID encountered while reverse-engineering the native protocol's compound
objects (`ValuesAll`, etc.) — used below to cross-validate the decoded layout against a live
controller.

## 4. `ConfigurationTable` and `ValuesAll` — compound object layout

`ValuesAll` (C.O. 24560) and friends (`ValueStatesAll`, `ValueStatesAndDataAll`,
`SetpointsAll`) are not a fixed schema — each individual value/setpoint's raw bytes live at
an offset determined by the controller's own `ConfigurationTable` (C.O. 24575, ~100KB on the
hardware this was validated against). Decoding one requires decoding the other first.

Reverse-engineered from decompiled `ComAp.Controller.dll`
(`ConfigurationTableLoaderIL3.LoadValueDescriptionFromStream`,
`CommonLoadValuesFromStream`), then byte-for-byte verified against a live controller's raw
`ConfigurationTable` and cross-checked against `cfgmodbus.txt`'s independently-exported
Modbus table (e.g. C.O. 8235 decodes to category `First`/type `Binary16` in both, and a live
read of "Mains Voltage L1-N" (C.O. 8195) decoded to a plausible 224V while "Generator
Voltage"/RPM read 0 — consistent with the generator being idle at capture time).

Implemented in `pycomap.configuration` for the **InteliLite3 (IL3)** binary format only
(`ControllerType` byte 14 at offset 6 of the table) — this is the only hardware it's been
validated against; other controller families (IGSNT, ID/IDMobile, etc.) use different binary
layouts and aren't supported.

**Value section** (offset 50 onward): four `uint16` counts (categories `First`/`Second`/
`Third`/`OneTime`), a redundant total count, four per-category data-lengths, a redundant
total data-length, three per-category state-lengths (no `OneTime` state), a redundant total
state-length, three `uint16` refresh periods (ms, one per non-`OneTime` category), then two
32-bit addresses: one to a flat list of value `Number`s (`uint16`, count = sum of all four
category counts, in category order), one to a flat array of fixed 13-byte detail records (one
per `Number`, same order):

- bytes 0-3 (`uint32` LE): bits 0-11 = `name_index` (12 bits, into the `CommonNames` heap
  category), bits 12-17 = `dim_index` (6 bits, into the `Dimensions` heap category), bits
  18-20 = `decimal_places` (3 bits), **bit 23 = `var_low_limit`**, **bit 24 = `var_high_limit`**
  — the remaining bits are conversion/switch metadata, not decoded.
  When `var_low_limit` / `var_high_limit` is set, the corresponding limit field holds a
  *setpoint index* (not a literal limit value) pointing to a setpoint that acts as the dynamic
  bound; ignore that limit for range validation purposes.
- bytes 4-7 (`uint32` LE): **bits 1-10 = `bit_name_index`** (10 bits, sentinel `1023` = none —
  for `BINARY*` types, the index into `CommonNames` of the first bit label; bit 0 → entry at
  `bit_name_index`, bit 1 → `bit_name_index + 1`, etc.), bits 11-20 = `state_index` (10 bits,
  sentinel `1023` = no state), bits 21-30 = `data_index` (10 bits) — both `state_index` and
  `data_index` are *absolute* offsets across the combined `First+Second+Third` region
- byte 8: `DataTypeIdentifier` (full byte)
- bytes 9-10, 11-12: low/high limit (`uint16` each, always present); for `INTEGER8`/`INTEGER16`/
  `INTEGER32` types the raw `uint16` is reinterpreted as `int16` (same 2-byte storage — IL3
  always uses 16-bit limits even for INTEGER32)

`decimal_places` (3 bits, max 7): a scaling exponent. The wire integer is divided by
`10^decimal_places` to get the physical value — e.g. `decimal_places=1`, raw wire `150` →
`15.0`. For `FLOAT` the stored bytes are IEEE-754 and `decimal_places` is always 0.

`STRING_LIST` values in `ValuesAll`: the raw 1-byte value is a direct option index with no
`low_limit` offset — unlike `STRING_LIST` *setpoints*, where `CommonNames[low_limit + wire_value]`
is the label. For values, use `BINARY*`-style bit queries or raw-byte inspection; there's no
`value_options()` API (values aren't writable, so the options list is informational only).

`OneTime` category values are excluded entirely from `ValuesAll`/`ValueStatesAndDataAll`.
`ValueStatesAndDataAll` is the data region (sized to the highest `data_index +
data_length` among non-`OneTime` values — gaps between values are possible, so this is *not*
simply the sum of all lengths) followed by the state region.

**`ValueStatesAll` byte layout**: one byte per value that has a `state_index` (sentinel `1023`
= not present); `state_index` is the *byte offset* into `ValueStatesAll`. Each byte:

| bits | field | encoding |
|------|-------|----------|
| 0-2 | `level1` | direct `ProtectionState` cast |
| 3-5 | `level2` | direct `ProtectionState` cast |
| 6-7 | `sensor_fail` | raw value left-shifted by 1: raw `1` → `ACTIVE`, raw `2` → `NOT_CONFIRMED` |

`ProtectionState` values: `NOT_ACTIVE=0`, `DELAY=1`, `ACTIVE=2`, `NOT_CONFIRMED=4` (combinable
flag — `ACTIVE | NOT_CONFIRMED` = 6 means the alarm is active but the operator hasn't pressed
Fault Reset yet). `ValueState.any_alarm` is True when any level's `ACTIVE` bit is set.
Implemented in `pycomap.configuration.decode_states_all`; exposed as
`Controller.read_value_states()`.

`DataTypeIdentifier` byte lengths (`DataTypeLength` in the decompiled source): 1 byte —
`Integer8`/`Unsigned8`/`Binary8`/`Char`/`StringList`; 2 bytes — `Integer16`/`Unsigned16`/
`Binary16`; 3 bytes — `Ftime`/`Fdate`; 4 bytes — `Integer32`/`Unsigned32`/`Float`/`Binary32`;
8 bytes — `Timer`; 16 bytes — `ShortString`/`IpAddress`; 32 bytes — `LongString`/
`TelephoneNumber`; 64 bytes — `HugeString`/`Email`. `Domain` and `Date` have no fixed length
and aren't decoded.

### 4.1 Names heap

`name_index`/`dim_index` resolve to human-readable strings through the "unified names heap"
(`ConfigurationTableLoaderIL3.InternalLoadNamesFromUnifiedHeap` in the decompiled source).
Verified end-to-end against a live controller: resolving `name_index`/`dim_index` for known
C.O.#s (8235, 8239, 8192, 10034, ...) reproduces `cfgmodbus.txt`'s names/dimensions exactly
(e.g. C.O. 8195 -> name `"Mains Voltage L1-N"`, dimension `"V"`).

There's one level of indirection: an "access vector" maps a 0-based index to a byte offset
into a separate "heap contents" blob of length-prefixed UTF-8 strings. Both are per-language;
this only decodes the first/default language.

- offset 169 (`DescrLangOffset`, IL3-specific): `uint32` address of language 0's record.
- that record's offset +6 (`NamesHeapAccessVectorOffset`): `uint32` address of the access
  vector. Offset +10 (`NamesHeapContentsOffset`): `uint32` address of the heap contents.
- access vector items are `uint16` if `ConfigFormatTerminal <= 3` (byte 5 of the table) else
  `uint32` (this controller: `ConfigFormatTerminal = 4`, so `uint32`).
- each names *category* (`CommonNames`, `Dimensions`, etc.) has its own fixed, absolute
  `(count_offset, base_index_offset)` pair, hardcoded per category in
  `ConfigurationTableLoaderIL3.GetNamesCategoryOffset` (base address `503`). All categories
  share one access vector + heap per language, at disjoint `[base_index, base_index + count)`
  ranges. Known categories:

  | Category | count_offset | base_index_offset | count type |
  |---|---|---|---|
  | `Dimensions` | 505 | 503 | 1-byte (`numNamesIsByte: true`) |
  | `GroupNames` | 515 | 513 | 1-byte |
  | `HistoryPrefixNames` | 525 | 523 | 1-byte |
  | `HistoryReasonNames` | 528 | 526 | `uint16` |
  | `AlarmReasonNames` | 532 | 530 | `uint16` |
  | `CommonNames` | 594 | 592 | `uint16` |

  `GroupNames` ordering within the `CreateNamesOffsetDescription` list: Dimensions (+0 bytes),
  FixedNames (+3), SetpointLimitNames (+7), GroupNames (+10) — each entry is 2 bytes for the
  `base_index_offset` plus 1 byte (byte count) or 2 bytes (uint16 count) for `count_offset`.

  `HistoryPrefixNames` on the test hardware: `['-', 'Wrn', 'Sd', 'Stp', 'LoP', 'Fls', 'OfL',
  'BOC', 'MP', 'Hst', 'ALI', 'AHI', 'ECU', 'BO']` — same heap used by both the alarm list
  (§4.3) and history records (§4.4). Index 0 is `'-'` (info/status, no protection class).
- to resolve index `j` in category `C`: read `uint16`/`uint32` at
  `access_vector_addr + item_size * (base_index[C] + j)` -> a byte offset into heap contents;
  at `heap_contents_addr + offset`, a single length byte followed by that many UTF-8 bytes is
  the name.

Implemented in `pycomap.configuration.parse_names_heap`; `parse_configuration_table` resolves
every value's `name`/`dimension` through it automatically.

### 4.2 Setpoints

`SetpointsAll` (C.O. 24559) follows the same "offset computed from `ConfigurationTable`"
pattern as values, but is simpler: there's no `OneTime`-style exclusion (every setpoint, `P`
or `R` category, is included) and no per-setpoint state.

Verified end-to-end against a live controller: decoding reproduces the exact, physically
sane configured values for e.g. C.O. 8276 "Nominal Power" -> 15.0 kW, C.O. 8277 "Nominal
Voltage Ph-N" -> 231V, C.O. 8253 "Nominal RPM" -> 3000 RPM — all matching `cfgmodbus.txt`'s
names/dimensions exactly.

**Setpoint section** (offset 98 onward): two `uint16` counts (categories `P`/`R`), a
redundant total count, two per-category data-lengths, a redundant total data-length, then two
32-bit addresses (id list, detail records) — same shape as the value section but with only
two categories and no state-length/refresh-period fields. Each detail record is a *fixed* 14
bytes (initially assumed variable-length because of conditionally-called helper methods in
the decompiled source — `SetSubstitutedSetpointInfo`, `SetSetpointDefaultValue`,
`SetSetpointIL3SpecificAttributes` — but all three save/restore the stream position around
their own absolute-offset reads, so none of them actually advance the main per-record
cursor):

- bytes 0-3 (`uint32` LE): bits 0-11 = `name_index`, bits 12-17 = `dim_index` (same heap
  categories as values), **bits 24-31 = `access_level`** (8 bits — 0 = no password required,
  non-zero = password required before the controller will accept a write)
- byte 4: bits 4-6 = `decimal_places` (3 bits)
- byte 5: `DataTypeIdentifier`
- bytes 6-9 (`uint32` LE): **bit 1 = `var_low_limit`**, **bit 2 = `var_high_limit`**
  (same semantics as the value record flags — when set, the corresponding limit is a setpoint
  index, not a literal value), bits 13-23 = `data_index` (11 bits, *absolute* offset across the
  combined `P+R` region)
- bytes 10-11, 12-13: low/high limit (`uint16` each, always present); same signed reinterpretation
  as value records for `INTEGER*` types

Implemented in `pycomap.configuration._parse_setpoints`/`decode_setpoints_all`.

Writing a setpoint is just `client.write_object(setpoint.number, encode_raw_value(...))` —
confirmed live (`8315` "Controller Mode", access level low enough to need no elevation;
`8301` "Emergency Start Delay", which did). The controller enforces per-setpoint
`access_level` (surfaced on `SetpointDescription.access_level`; `needs_password` is True
when non-zero) — see §2.4.1 for how to raise the session's access level via
`ComApClient.elevate_access` before writing a setpoint that requires it. `encode_raw_value`
is the write-side inverse of `decode_raw_value`; the controller itself rejects out-of-range
writes with `ControllerError.BAD_WRITE_VALUE`.

`STRING_LIST` values and setpoints: the wire value is a 0-based index offset from `low_limit`
into `CommonNames` — `label = CommonNames[low_limit + wire_value]`. Valid wire range is
`0 .. (high_limit - low_limit)` (unless `var_high_limit` is set). `Controller.read_values()`
resolves these to their label strings automatically; `Controller.value_label(name, wire_value)`
resolves a single value. Setpoint options are exposed via
`Controller.setpoint_options(name_or_number)` → `[(wire_value, label), ...]`.

Not yet implemented:
- `String`/`Domain`/`Timer`/`Date`-typed values: returned as raw bytes by
  `pycomap.configuration.decode_raw_value`, not decoded further (their `name`/`dimension` are
  still resolved correctly, only the data payload isn't).

### 4.3 Alarm list

`AlarmList` (C.O. 24545, 112 bytes) is a flat array of up to **16 × 7-byte** records
(remaining slots are zeroed). Each 7-byte record: `uint32` dw + `uint16` flags + `uint8`
source. Parsing stops at the first unused slot.

**`is_used`**: bit 31 of `dw` must be 1, *and* the record must not be the all-`0xFF` sentinel
(`dw==0xFFFFFFFF and flags==0xFFFF and source==0xFF`).

**`flags` bit layout:**

| bits | field |
|---|---|
| 0-2 | `kind` — `7` = ComAp (standard); other values = ECU/CAN alarms |
| 3-13 | `reason_index` — index into `AlarmReasonNames` heap category |
| 14 | `is_active` |
| 15 | `is_confirmed` |

**`dw` bit layout:**

| bits | field |
|---|---|
| 0-18 | `fault_code` — raw ECU fault code (non-zero only for non-ComAp kinds) |
| 19-23 | `prefix_index` — index into `HistoryPrefixNames` heap category |
| 24-30 | `occurred` — occurrence counter |
| 31 | `is_used` sentinel (must be 1) |

For `kind == 7` (ComAp): `reason = AlarmReasonNames[reason_index]`, `prefix =
HistoryPrefixNames[prefix_index]`. For other kinds: `reason` and `prefix` are empty; the ECU
fault code is in `fault_code`.

Implemented in `pycomap.alarms.parse_alarm_list`; exposed as `Controller.read_alarms()`.
`HistoryPrefixNames` heap contents and offsets: see §4.1.

### 4.4 History records

`YoungestHistoryRecord` (C.O. 24569) and `OlderHistoryRecord` (C.O. 24567) each return one
**69-byte** record. Fetch in sequence to walk backward through the ring buffer.

**Wire layout** (`ClientDrivenHistorySerializer.LoadHeaderIL3` + `HistoryTimeStamp.LoadDefinedByHistRecord` in `ComAp.Controller.dll`):

| bytes | field |
|---|---|
| 0-1 | `uint16` LE — bits 0-11 = `reason_index`, bits 13-14 = `reason_category` |
| 2 | bits 0-4 = `prefix_index`, bits 5-7 = `level` |
| 3-11 | 9-byte timestamp (see below) |
| 12-68 | 57-byte payload (see below) |

`prefix_index` sentinels: **30** = text record (payload is null-terminated ASCII); **31** =
invalid/unused slot, skip.

`reason_category`: 0 = `HistoryReasonNames`, 1 = `CommonNames`, 2 = `DiagNames` (ECU
diagnostic codes — not yet implemented, returns empty string), 3 = `AlarmReasonNames`.

`prefix_index = 0` maps to `'-'` (info/status event, no protection class). `HistoryPrefixNames`
heap contents and offsets: see §4.1.

**Timestamp (9 bytes, `DefinedByHistRecord` format):**

| byte(s) | field |
|---|---|
| 0 | BCD(day) |
| 1 | BCD(month) |
| 2 | BCD(year − 2000) |
| 3 | BCD(hour) |
| 4 | BCD(minute) |
| 5 | BCD(second) |
| 6 | bit 7 = type (0 = wall-clock RTC, 1 = engine-hours counter); bits 0-3 = tenths-of-second |
| 7-8 | `uint16` LE = sequential record index (ring-buffer position) |

For engine-hours records, bytes 0-3 reinterpret as a single `uint32` LE where bits 0-23 =
total hours and bits 24-31 = minutes.

**57-byte payload:**

- **Text records** (`prefix_index == 30`): null-terminated ASCII string describing the
  configuration change (e.g. `"T=ETH CA1 A CON(24554)=21:25:08"`).
- **Alarm/event records**: a snapshot of the first 57 bytes of `ValuesAll`, captured at the
  moment of the event. The byte layout is identical to the live `ValuesAll` blob — each
  value's raw bytes sit at its `data_index` byte offset, with the same data type and
  decimal-place encoding. Values whose `data_index + data_length > 57` are absent from the
  snapshot. On the test hardware this covers 31 values: `Binary Inputs` (data_index=0) through
  `Load Power Factor` (data_index=56, 1 byte). Decoded via
  `pycomap.configuration.decode_history_snapshot(table, record.data)` or
  `Controller.decode_history_snapshot(record)`.

### 4.5 Group table

The `ConfigurationTable` contains a `GroupDescription` section that assigns every value and
setpoint to a human-readable group (Engine, Generator, Load, Mains, Controller I/O, Statistics,
Invisible, CM-4G-GPS, …). This is what InteliConfig uses for its "Group / Subgroup" columns
and what the controller front panel uses to organise its menu.

Source: `ConfigurationTableLoaderIL3.LoadGroupDescriptionFromStream` and
`ConfigurationTableLoader.CommonLoadGroupsFromStream` in `ComAp.Controller.dll`.

**Header (IL3-specific fixed offsets):**

- offset 134: `uint16` — number of groups
- offset 136: `uint32` — absolute offset of the `GroupDescription` records array

**Per-`GroupDescription` record (11 bytes):**

| bytes | field |
|---|---|
| 0-1 (`uint16` w1) | bits 0-7 = `contents_id`; bits 8-12 = `num_subgroups`; bit 13 = `is_invisible_internal` |
| 2-3 (`uint16` w2) | bits 0-8 = value-hiding condition index; bits 9-15 = `num_items` (7 bits) |
| 4-5 (`uint16` w3) | bits 0-8 = setpoint-hiding condition index; bits 9-14 = `name_idx` (6 bits into `GroupNames`); bit 15 = `is_fast_access` |
| 6-7 (`uint16`) | `items_offset` — absolute offset of this group's item list |
| 8-9 (`uint16`) | `subgroups_offset` — absolute offset of this group's subgroup list |
| 10 (byte) | bit 0 = `is_sealed`; bit 1 = `is_invisible_external` |

Group name: `GroupNames[name_idx]` (see §4.1 for the `GroupNames` heap offsets).

**Per-item record (4 bytes):**

| bytes | field |
|---|---|
| 0-1 (`uint16` iw1) | bits 0-1 = `CommunicationObjectType` (0 = value, 1 = setpoint); bits 2-12 = `object_index` (0-based index into the values or setpoints array) |
| 2-3 (`uint16` iw2) | bits 0-10 = visibility condition index |

`GroupTableBaseOffset = 0` for IL3 — `items_offset` and `subgroups_offset` are absolute offsets
into the `ConfigurationTable` blob.

**Coverage on the test hardware (FV 15000, 34 groups total):**

All 325 values and all 429 setpoints appear in exactly one group. Notable groups: `Engine` (18
values), `Generator` (11), `Load` (23), `Mains` (7), `Controller I/O` (8), `Statistics` (19),
`Invisible` (102 — internal signals, excluded from the `status.py` example by default),
`PLC` (47), `CM-4G-GPS` (14).

Implemented in `pycomap.configuration._parse_group_map`; `parse_configuration_table`
populates `ValueDescription.group` / `SetpointDescription.group` (`str | None`) automatically.
