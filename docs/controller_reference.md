---
hide:
  - navigation
---

# ComAp Controller Reference

## Values

| # | Category | Group | Name | Type | Unit | Value |
| --- | --- | --- | --- | --- | --- | --- |
| 8192 | SECOND | Generator | Generator Voltage L1-N | UNSIGNED16 | V | 0 |
| 8193 | SECOND | Generator | Generator Voltage L2-N | UNSIGNED16 | V | 0 |
| 8194 | SECOND | Generator | Generator Voltage L3-N | UNSIGNED16 | V | 0 |
| 8195 | SECOND | Mains | Mains Voltage L1-N | UNSIGNED16 | V | 233 |
| 8196 | SECOND | Mains | Mains Voltage L2-N | UNSIGNED16 | V | 0 |
| 8197 | SECOND | Mains | Mains Voltage L3-N | UNSIGNED16 | V | 0 |
| 8198 | SECOND | Load | Load A L1 | UNSIGNED16 | A | 0 |
| 8199 | SECOND | Load | Load A L2 | UNSIGNED16 | A | 0 |
| 8200 | SECOND | Load | Load A L3 | UNSIGNED16 | A | 0 |
| 8202 | SECOND | Load | Load kW | INTEGER16 | kW | 0 |
| 8203 | SECOND | Load | Load kVAr | INTEGER16 | kVAr | 0 |
| 8204 | SECOND | Load | Load Power Factor | INTEGER8 |  | 0 |
| 8205 | THIRD | Statistics | Genset kWh | INTEGER32 | kWh | 19 |
| 8206 | THIRD | Statistics | Running Hours | INTEGER32 | h | 55.04 |
| 8207 | THIRD | Statistics | Num Starts | UNSIGNED16 |  | 351 |
| 8210 | SECOND | Generator | Generator Frequency | UNSIGNED16 | Hz | 0 |
| 8211 | SECOND | Mains | Mains Frequency | UNSIGNED16 | Hz | 5 |
| 8213 | THIRD | Controller I/O | BatteryVoltage | INTEGER16 | V | 1.27 |
| 8235 | FIRST | Controller I/O | Binary Inputs | BINARY16 |  | 2 |
| 8239 | FIRST | Controller I/O | Binary Outputs | BINARY16 |  | 0 |
| 8395 | SECOND | Load | Load Characteristic | CHAR |  | 20 |
| 8450 | THIRD | Invisible | IgMax | UNSIGNED16 | A | 7.5 |
| 8451 | THIRD | Invisible | ST | UNSIGNED16 |  | 277 |
| 8452 | THIRD | Invisible | ST | UNSIGNED16 |  | 161 |
| 8453 | THIRD | Invisible | ST | UNSIGNED16 |  | 277 |
| 8454 | THIRD | Invisible | ST | UNSIGNED16 |  | 138 |
| 8480 | ONE_TIME | IL Info | Application | STRING_LIST |  | — |
| 8524 | SECOND | Load | Load kW L1 | INTEGER16 | kW | 0 |
| 8525 | SECOND | Load | Load kW L2 | INTEGER16 | kW | 0 |
| 8526 | SECOND | Load | Load kW L3 | INTEGER16 | kW | 0 |
| 8527 | SECOND | Load | Load kVAr L1 | INTEGER16 | kVAr | 0 |
| 8528 | SECOND | Load | Load kVAr L2 | INTEGER16 | kVAr | 0 |
| 8529 | SECOND | Load | Load kVAr L3 | INTEGER16 | kVAr | 0 |
| 8530 | SECOND | Load | Load kVA L1 | INTEGER16 | kVA | 0 |
| 8531 | SECOND | Load | Load kVA L2 | INTEGER16 | kVA | 0 |
| 8532 | SECOND | Load | Load kVA L3 | INTEGER16 | kVA | 0 |
| 8533 | SECOND | Load | Load Power Factor L1 | INTEGER8 |  | 0 |
| 8534 | SECOND | Load | Load Power Factor L2 | INTEGER8 |  | 0 |
| 8535 | SECOND | Load | Load Power Factor L3 | INTEGER8 |  | 0 |
| 8539 | THIRD | Statistics | Genset kVArh | INTEGER32 | kVArh | 97.51 |
| 8565 | SECOND | Load | Load kVA | INTEGER16 | kVA | 0 |
| 8626 | SECOND | Load | Load Characteristic L1 | CHAR |  | 20 |
| 8627 | SECOND | Load | Load Characteristic L2 | CHAR |  | 20 |
| 8628 | SECOND | Load | Load Characteristic L3 | CHAR |  | 20 |
| 8707 | ONE_TIME | IL Info | FW Branch | STRING_LIST |  | — |
| 8955 | FIRST | Invisible | Timer Value | UNSIGNED16 |  | 0 |
| 9018 | SECOND | Generator | Nominal Power | INTEGER16 | kW | 1.5 |
| 9040 | THIRD | Statistics | Total Fuel Consumption | UNSIGNED32 | L | 0 |
| 9143 | FIRST | Log Bout | Log Bout 1 | BINARY16 |  | 0 |
| 9144 | FIRST | Log Bout | Log Bout 2 | BINARY16 |  | 8248 |
| 9145 | SECOND | Log Bout | Log Bout 3 | BINARY16 |  | 4224 |
| 9146 | SECOND | Log Bout | Log Bout 4 | BINARY16 |  | 0 |
| 9147 | SECOND | Log Bout | Log Bout 5 | BINARY16 |  | 0 |
| 9148 | SECOND | Log Bout | Log Bout 6 | BINARY16 |  | 304 |
| 9149 | SECOND | Log Bout | Log Bout 7 | BINARY16 |  | 4 |
| 9150 | SECOND | Log Bout | Log Bout 8 | BINARY16 |  | 0 |
| 9151 | THIRD | Controller I/O | Not Used | INTEGER16 |  | -32768 |
| 9152 | THIRD | Controller I/O | Not Used | INTEGER16 |  | -32768 |
| 9153 | THIRD | Controller I/O | Not Used | INTEGER16 |  | -32768 |
| 9154 | THIRD | Controller I/O | Not Used | INTEGER16 |  | -32768 |
| 9244 | FIRST | IL Info | Engine State | STRING_LIST |  | Ready |
| 9245 | FIRST | IL Info | Breaker State | STRING_LIST |  | MainsOper |
| 9628 | SECOND | Generator | Generator Voltage L1-L2 | UNSIGNED16 | V | 0 |
| 9629 | SECOND | Generator | Generator Voltage L2-L3 | UNSIGNED16 | V | 0 |
| 9630 | SECOND | Generator | Generator Voltage L3-L1 | UNSIGNED16 | V | 0 |
| 9631 | SECOND | Mains | Mains Voltage L1-L2 | UNSIGNED16 | V | 0 |
| 9632 | SECOND | Mains | Mains Voltage L2-L3 | UNSIGNED16 | V | 0 |
| 9633 | SECOND | Mains | Mains Voltage L3-L1 | UNSIGNED16 | V | 0 |
| 9887 | FIRST | Invisible | Controler Mode | STRING_LIST |  | AUTO |
| 9917 | THIRD | Generator | Nominal Voltage | UNSIGNED16 | V | 231 |
| 9978 | THIRD | Generator | Nominal Current | UNSIGNED16 | A | 6.3 |
| 10006 | SECOND | Engine | SpeedReq RPM | UNSIGNED16 | RPM | 900 |
| 10034 | FIRST | Engine | ECU State | BINARY8 | - | 0 |
| 10040 | FIRST | IL Info | Timer Text | STRING_LIST |  | No Timer |
| 10123 | SECOND | Engine | RPM | INTEGER16 | RPM | 0 |
| 10124 | THIRD | Invisible | CU Temperature | INTEGER16 | °C | 15.64 |
| 10137 | SECOND | Engine | Speed Request | INTEGER16 | % | 5 |
| 10153 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10154 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10155 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10156 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10157 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10158 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10159 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10160 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10161 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10162 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10163 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10164 | THIRD | Engine | Not Used | INTEGER16 | - | -32768 |
| 10165 | THIRD | Invisible | ECU-BIN 13 | INTEGER16 | - | -32768 |
| 10166 | THIRD | Invisible | ECU-BIN 14 | INTEGER16 | - | -32768 |
| 10167 | THIRD | Invisible | ECU-BIN 15 | INTEGER16 | - | -32768 |
| 10168 | THIRD | Invisible | ECU-BIN 16 | INTEGER16 | - | -32768 |
| 10169 | SECOND | Invisible | ecu_bin_0 | BINARY8 | - | 0 |
| 10170 | SECOND | Invisible | ecu_bin_1 | BINARY8 | - | 0 |
| 10171 | SECOND | Invisible | ECU BOUT1 | BINARY8 | - | 0 |
| 10172 | SECOND | Invisible | ECU BOUT2 | BINARY8 | - | 0 |
| 10173 | THIRD | Engine | Not Used | INTEGER32 | - | -2147483648 |
| 10232 | THIRD | Invisible | ECU FC | UNSIGNED32 |  | 0 |
| 10233 | THIRD | Invisible | ECU FMI | UNSIGNED8 |  | 0 |
| 10360 | SECOND | PLC | PLC-AOUT 1 | INTEGER16 |  | -32768 |
| 10361 | SECOND | PLC | PLC-AOUT 2 | INTEGER16 |  | -32768 |
| 10362 | SECOND | PLC | PLC-AOUT 3 | INTEGER16 |  | -32768 |
| 10363 | SECOND | PLC | PLC-AOUT 4 | INTEGER16 |  | -32768 |
| 10364 | SECOND | PLC | PLC-AOUT 5 | INTEGER16 |  | -32768 |
| 10365 | SECOND | PLC | PLC-AOUT 6 | INTEGER16 |  | -32768 |
| 10366 | SECOND | PLC | PLC-AOUT 7 | INTEGER16 |  | -32768 |
| 10367 | SECOND | PLC | PLC-AOUT 8 | INTEGER16 |  | -32768 |
| 10368 | SECOND | PLC | PLC-AOUT 9 | INTEGER16 |  | -32768 |
| 10369 | SECOND | PLC | PLC-AOUT 10 | INTEGER16 |  | -32768 |
| 10370 | SECOND | PLC | PLC-AOUT 11 | INTEGER16 |  | -32768 |
| 10371 | SECOND | PLC | PLC-AOUT 12 | INTEGER16 |  | -32768 |
| 10372 | SECOND | PLC | PLC-AOUT 13 | INTEGER16 |  | -32768 |
| 10373 | SECOND | PLC | PLC-AOUT 14 | INTEGER16 |  | -32768 |
| 10374 | SECOND | PLC | PLC-AOUT 15 | INTEGER16 |  | -32768 |
| 10375 | SECOND | PLC | PLC-AOUT 16 | INTEGER16 |  | -32768 |
| 10376 | SECOND | PLC | PLC-AOUT 17 | INTEGER16 |  | -32768 |
| 10377 | SECOND | PLC | PLC-AOUT 18 | INTEGER16 |  | -32768 |
| 10378 | SECOND | PLC | PLC-AOUT 19 | INTEGER16 |  | -32768 |
| 10379 | SECOND | PLC | PLC-AOUT 20 | INTEGER16 |  | -32768 |
| 10380 | SECOND | PLC | PLC-AOUT 21 | INTEGER16 |  | -32768 |
| 10381 | SECOND | PLC | PLC-AOUT 22 | INTEGER16 |  | -32768 |
| 10382 | SECOND | PLC | PLC-AOUT 23 | INTEGER16 |  | -32768 |
| 10383 | SECOND | PLC | PLC-AOUT 24 | INTEGER16 |  | -32768 |
| 10384 | SECOND | PLC | PLC-AOUT 25 | INTEGER16 |  | -32768 |
| 10385 | SECOND | PLC | PLC-AOUT 26 | INTEGER16 |  | -32768 |
| 10386 | SECOND | PLC | PLC-AOUT 27 | INTEGER16 |  | -32768 |
| 10387 | SECOND | PLC | PLC-AOUT 28 | INTEGER16 |  | -32768 |
| 10388 | SECOND | PLC | PLC-AOUT 29 | INTEGER16 |  | -32768 |
| 10389 | SECOND | PLC | PLC-AOUT 30 | INTEGER16 |  | -32768 |
| 10390 | SECOND | PLC | PLC-AOUT 31 | INTEGER16 |  | -32768 |
| 10391 | SECOND | PLC | PLC-AOUT 32 | INTEGER16 |  | -32768 |
| 10424 | SECOND | PLC | PLC-BOUT 1 | BINARY8 |  | 0 |
| 10425 | SECOND | PLC | PLC-BOUT 2 | BINARY8 |  | 0 |
| 10426 | SECOND | PLC | PLC-BOUT 3 | BINARY8 |  | 0 |
| 10427 | SECOND | PLC | PLC-BOUT 4 | BINARY8 |  | 0 |
| 10428 | SECOND | PLC | PLC-BOUT 5 | BINARY8 |  | 0 |
| 10429 | SECOND | PLC | PLC-BOUT 6 | BINARY8 |  | 0 |
| 10430 | SECOND | PLC | PLC-BOUT 7 | BINARY8 |  | 0 |
| 10504 | SECOND | PLC | PLC Resource 1 | UNSIGNED16 |  | 0 |
| 10505 | SECOND | PLC | PLC Resource 2 | UNSIGNED16 |  | 0 |
| 10506 | SECOND | PLC | PLC Resource 3 | UNSIGNED16 |  | 0 |
| 10507 | SECOND | PLC | PLC Resource 4 | UNSIGNED16 |  | 0 |
| 10508 | SECOND | PLC | PLC Resource 5 | UNSIGNED16 |  | 0 |
| 10509 | SECOND | PLC | PLC Resource 6 | UNSIGNED16 |  | 0 |
| 10510 | SECOND | PLC | PLC Resource 7 | UNSIGNED16 |  | 0 |
| 10511 | SECOND | PLC | PLC Resource 8 | UNSIGNED16 |  | 0 |
| 10603 | THIRD | Controller I/O | D+ | INTEGER16 | V | 0 |
| 10688 | THIRD | Invisible | ECU-BIN 17 | INTEGER16 | - | -32768 |
| 10689 | THIRD | Invisible | ECU-BIN 18 | INTEGER16 | - | -32768 |
| 10690 | THIRD | Invisible | ECU-BIN 19 | INTEGER16 | - | -32768 |
| 10691 | THIRD | Invisible | ECU-BIN 20 | INTEGER16 | - | -32768 |
| 10692 | THIRD | Invisible | ECU-BIN 21 | INTEGER16 | - | -32768 |
| 10693 | THIRD | Invisible | ECU-BIN 22 | INTEGER16 | - | -32768 |
| 10694 | THIRD | Invisible | ECU-BIN 23 | INTEGER16 | - | -32768 |
| 10695 | THIRD | Invisible | ECU-BIN 24 | INTEGER16 | - | -32768 |
| 10696 | THIRD | Invisible | ECU-BIN 25 | INTEGER16 | - | -32768 |
| 10697 | THIRD | Invisible | ECU-BIN 26 | INTEGER16 | - | -32768 |
| 10698 | THIRD | Invisible | ECU-BIN 27 | INTEGER16 | - | -32768 |
| 10699 | THIRD | Invisible | ECU-BIN 28 | INTEGER16 | - | -32768 |
| 10700 | THIRD | Invisible | ECU-BIN 29 | INTEGER16 | - | -32768 |
| 10701 | THIRD | Invisible | ECU-BIN 30 | INTEGER16 | - | -32768 |
| 10702 | THIRD | Invisible | ECU-BIN 31 | INTEGER16 | - | -32768 |
| 10703 | THIRD | Invisible | ECU-BIN 32 | INTEGER16 | - | -32768 |
| 10752 | SECOND | Invisible | ecu_bin_2 | BINARY8 | - | 0 |
| 10753 | SECOND | Invisible | ecu_bin_3 | BINARY8 | - | 0 |
| 10760 | SECOND | Invisible | ECU BOUT3 | BINARY8 | - | 0 |
| 10761 | SECOND | Invisible | ECU BOUT4 | BINARY8 | - | 0 |
| 10986 | THIRD | Statistics | Pulse Counter 1 | UNSIGNED32 |   | 0 |
| 10987 | THIRD | Statistics | Pulse Counter 2 | UNSIGNED32 |   | 0 |
| 11025 | THIRD | Statistics | Mains kWh | INTEGER32 | kWh | 0 |
| 11026 | THIRD | Statistics | Mains kVArh | INTEGER32 | kVArh | 0 |
| 11195 | THIRD | Statistics | Num E-Stops | UNSIGNED32 |  | 1 |
| 11196 | THIRD | Statistics | Shutdowns | UNSIGNED32 |  | 23 |
| 11388 | THIRD | Invisible | ST | BINARY32 |  | 5696 |
| 11616 | THIRD | Statistics | Maintenance 1 | INTEGER16 | h | 5 |
| 11617 | THIRD | Statistics | Maintenance 2 | INTEGER16 | h | 10000 |
| 11618 | THIRD | Statistics | Maintenance 3 | INTEGER16 | h | 10000 |
| 11680 | THIRD | CM-4G-GPS | HomePosDist | UNSIGNED32 | km | 4.29497e+07 |
| 11896 | SECOND | Log Bout | Log Bout 9 | BINARY16 |  | 0 |
| 11897 | SECOND | Log Bout | Log Bout 10 | BINARY16 |  | 512 |
| 11898 | SECOND | Log Bout | Log Bout 11 | BINARY16 |  | 0 |
| 11899 | SECOND | Log Bout | Log Bout 12 | BINARY16 |  | 0 |
| 12475 | THIRD | Invisible | ST | UNSIGNED32 |  | 2693791776 |
| 12482 | FIRST | Invisible | DPF_status | BINARY32 |  | 0 |
| 12483 | THIRD | Invisible | DPF1 Ash Load | UNSIGNED16 | % | 0 |
| 12926 | THIRD | Engine | ECU FreqSelect | UNSIGNED16 |  | 0 |
| 12944 | SECOND | IL Info | Connection Type | STRING_LIST |  | MonoPhase |
| 13770 | THIRD | Statistics | Time Till Empty | INTEGER16 | min | -32768 |
| 13771 | THIRD | Statistics | Time Till Empty | INTEGER16 | hrs | -32768 |
| 13772 | THIRD | Statistics | Time Till Empty | INTEGER16 | day | -32768 |
| 14050 | THIRD | Invisible | ST | UNSIGNED16 |  | 161 |
| 14051 | THIRD | Invisible | ST | UNSIGNED16 |  | 277 |
| 14052 | THIRD | Invisible | ST | UNSIGNED16 |  | 0 |
| 14053 | THIRD | Invisible | ST | UNSIGNED16 |  | 0 |
| 14054 | THIRD | Invisible | ST | UNSIGNED16 |  | 161 |
| 14055 | THIRD | Invisible | ST | UNSIGNED16 |  | 277 |
| 14056 | THIRD | Invisible | ST | UNSIGNED16 |  | 138 |
| 14057 | THIRD | Invisible | ST | UNSIGNED16 |  | 277 |
| 14291 | FIRST | Plug-in IO | EM BIO A | BINARY16 |  | 0 |
| 14292 | FIRST | Plug-in IO | EM BIO B | BINARY16 |  | 0 |
| 14293 | SECOND | Plug-in IO | EM Analog Input A 1 | INTEGER16 |  | 0 |
| 14294 | SECOND | Plug-in IO | EM Analog Input A 2 | INTEGER16 |  | 0 |
| 14295 | SECOND | Plug-in IO | EM Analog Input A 3 | INTEGER16 |  | 0 |
| 14296 | SECOND | Plug-in IO | EM Analog Input A 4 | INTEGER16 |  | 0 |
| 14297 | SECOND | Plug-in IO | EM Analog Input A 5 | INTEGER16 |  | 0 |
| 14298 | SECOND | Plug-in IO | EM Analog Input A 6 | INTEGER16 |  | 0 |
| 14299 | SECOND | Plug-in IO | EM Analog Input A 7 | INTEGER16 |  | 0 |
| 14300 | SECOND | Plug-in IO | EM Analog Input A 8 | INTEGER16 |  | 0 |
| 14301 | SECOND | Plug-in IO | EM Analog Input A 9 | INTEGER16 |  | 0 |
| 14302 | SECOND | Plug-in IO | EM Analog Input A 10 | INTEGER16 |  | 0 |
| 14303 | SECOND | Plug-in IO | EM Analog Input A 11 | INTEGER16 |  | 0 |
| 14304 | SECOND | Plug-in IO | EM Analog Input A 12 | INTEGER16 |  | 0 |
| 14305 | SECOND | Plug-in IO | EM Analog Input A 13 | INTEGER16 |  | 0 |
| 14306 | SECOND | Plug-in IO | EM Analog Input A 14 | INTEGER16 |  | 0 |
| 14307 | SECOND | Plug-in IO | EM Analog Input A 15 | INTEGER16 |  | 0 |
| 14308 | SECOND | Plug-in IO | EM Analog Input A 16 | INTEGER16 |  | 0 |
| 14309 | SECOND | Plug-in IO | EM Analog Input B 1 | INTEGER16 |  | 0 |
| 14310 | SECOND | Plug-in IO | EM Analog Input B 2 | INTEGER16 |  | 0 |
| 14311 | SECOND | Plug-in IO | EM Analog Input B 3 | INTEGER16 |  | 0 |
| 14312 | SECOND | Plug-in IO | EM Analog Input B 4 | INTEGER16 |  | 0 |
| 14313 | SECOND | Plug-in IO | EM Analog Input B 5 | INTEGER16 |  | 0 |
| 14314 | SECOND | Plug-in IO | EM Analog Input B 6 | INTEGER16 |  | 0 |
| 14315 | SECOND | Plug-in IO | EM Analog Input B 7 | INTEGER16 |  | 0 |
| 14316 | SECOND | Plug-in IO | EM Analog Input B 8 | INTEGER16 |  | 0 |
| 14317 | SECOND | Plug-in IO | EM Analog Input B 9 | INTEGER16 |  | 0 |
| 14318 | SECOND | Plug-in IO | EM Analog Input B 10 | INTEGER16 |  | 0 |
| 14319 | SECOND | Plug-in IO | EM Analog Input B 11 | INTEGER16 |  | 0 |
| 14320 | SECOND | Plug-in IO | EM Analog Input B 12 | INTEGER16 |  | 0 |
| 14321 | SECOND | Plug-in IO | EM Analog Input B 13 | INTEGER16 |  | 0 |
| 14322 | SECOND | Plug-in IO | EM Analog Input B 14 | INTEGER16 |  | 0 |
| 14323 | SECOND | Plug-in IO | EM Analog Input B 15 | INTEGER16 |  | 0 |
| 14324 | SECOND | Plug-in IO | EM Analog Input B 16 | INTEGER16 |  | 0 |
| 14325 | SECOND | Generator | Earth Fault Current | INTEGER16 | A | 0 |
| 14328 | THIRD | Statistics | Rental 1 | INTEGER32 | h | 0 |
| 14369 | THIRD | Statistics | Rental 2 | INTEGER32 | day | 26473 |
| 14389 | THIRD | Invisible | CU Analog Input 1 Wrn Level | INTEGER16 |  | -32768 |
| 14390 | THIRD | Invisible | CU Analog Input 2 Wrn Level | INTEGER16 |  | -32768 |
| 14391 | THIRD | Invisible | CU Analog Input 3 Wrn Level | INTEGER16 |  | -32768 |
| 14392 | THIRD | Invisible | CU Analog Input 4 Wrn Level | INTEGER16 |  | -32768 |
| 14393 | THIRD | Invisible | CU Analog Input 1 Lim Level | INTEGER16 |  | -32768 |
| 14394 | THIRD | Invisible | CU Analog Input 2 Lim Level | INTEGER16 |  | -32768 |
| 14395 | THIRD | Invisible | CU Analog Input 3 Lim Level | INTEGER16 |  | -32768 |
| 14396 | THIRD | Invisible | CU Analog Input 4 Lim Level | INTEGER16 |  | -32768 |
| 14423 | THIRD | Invisible | CM and EM modules | UNSIGNED32 |  | 16 |
| 14446 | FIRST | Invisible | Application Mode | STRING_LIST |  | AMF |
| 14447 | THIRD | IL Info | SPI Module A | STRING_LIST |  | CM-Ethernet |
| 14448 | THIRD | IL Info | SPI Module B | STRING_LIST |  | Empty |
| 14515 | SECOND | Invisible | ST | INTEGER16 | kW | 1.8 |
| 14516 | SECOND | Invisible | ST | INTEGER16 | kW | 1.8 |
| 14522 | THIRD | Invisible | DEF Level | INTEGER16 | % | 0 |
| 14779 | THIRD | Invisible | ST | UNSIGNED16 |  | 265 |
| 14780 | THIRD | Invisible | ST | UNSIGNED16 |  | 196 |
| 14783 | THIRD | Invisible | ST | UNSIGNED16 |  | 196 |
| 14784 | THIRD | Invisible | ST | UNSIGNED16 |  | 265 |
| 14787 | THIRD | Invisible | ST | UNSIGNED16 |  | 196 |
| 14788 | THIRD | Invisible | ST | UNSIGNED16 |  | 265 |
| 15352 | THIRD | Invisible | Seconds | UNSIGNED8 | s | 31 |
| 15353 | THIRD | Invisible | Minutes | UNSIGNED8 | m | 51 |
| 15354 | THIRD | Invisible | Hours | UNSIGNED8 | h | 14 |
| 15355 | THIRD | Invisible | Month | UNSIGNED8 |   | 7 |
| 15356 | THIRD | Invisible | Day | UNSIGNED8 |   | 10 |
| 15357 | THIRD | Invisible | Years since 1985 | UNSIGNED8 |   | 41 |
| 15378 | FIRST | Invisible | DPF_status | BINARY32 |  | 0 |
| 15765 | THIRD | Invisible | DPF1 Soot Load | INTEGER16 | % | 0 |
| 15780 | FIRST | Invisible | E-STOP | BINARY8 |  | 1 |
| 15870 | SECOND | Invisible | Generator Frequency RAW | UNSIGNED16 | Hz | 0 |
| 15871 | SECOND | Invisible | Generator Voltage L1-N RAW | UNSIGNED16 | V | 0 |
| 15872 | SECOND | Invisible | Generator Voltage L2-N RAW | UNSIGNED16 | V | 0 |
| 15873 | SECOND | Invisible | Generator Voltage L3-N RAW | UNSIGNED16 | V | 0 |
| 15874 | SECOND | Invisible | Generator Voltage L1-L2 RAW | UNSIGNED16 | V | 0 |
| 15875 | SECOND | Invisible | Generator Voltage L2-L3 RAW | UNSIGNED16 | V | 0 |
| 15876 | SECOND | Invisible | Generator Voltage L3-L1 RAW | UNSIGNED16 | V | 0 |
| 15877 | SECOND | Invisible | Load kVA RAW | INTEGER16 | kVA | 0 |
| 15878 | SECOND | Invisible | Load kVA L1 RAW | INTEGER16 | kVA | 0 |
| 15879 | SECOND | Invisible | Load kVA L2 RAW | INTEGER16 | kVA | 0 |
| 15880 | SECOND | Invisible | Load kVA L3 RAW | INTEGER16 | kVA | 0 |
| 15881 | SECOND | Invisible | Load kVAr RAW | INTEGER16 | kVAr | 0 |
| 15882 | SECOND | Invisible | Load kVAr L1 RAW | INTEGER16 | kVAr | 0 |
| 15883 | SECOND | Invisible | Load kVAr L2 RAW | INTEGER16 | kVAr | 0 |
| 15884 | SECOND | Invisible | Load kVAr L3 RAW | INTEGER16 | kVAr | 0 |
| 15885 | SECOND | Invisible | Load kW RAW | INTEGER16 | kW | 0 |
| 15886 | SECOND | Invisible | Load kW L1 RAW | INTEGER16 | kW | 0 |
| 15887 | SECOND | Invisible | Load kW L2 RAW | INTEGER16 | kW | 0 |
| 15888 | SECOND | Invisible | Load kW L3 RAW | INTEGER16 | kW | 0 |
| 16044 | THIRD | Dual Operation | Master Running Hours | INTEGER32 | h | -2.14748e+07 |
| 16045 | THIRD | Dual Operation | Slave Running Hours | INTEGER32 | h | -2.14748e+07 |
| 16046 | THIRD | Dual Operation | Running Hours To Swap | INTEGER16 | h | -327.68 |
| 24146 | THIRD | CM-4G-GPS | Connection Type | SHORT_STRING |  |  |
| 24147 | THIRD | CM-4G-GPS | Operator | LONG_STRING |  |  |
| 24180 | SECOND | CM-Ethernet | ETH Interface Status | STRING_LIST |  | Connected |
| 24181 | THIRD | CM-Ethernet | Current DNS | SHORT_STRING |  | 192.168.1.3 |
| 24182 | THIRD | CM-Ethernet | Current Gateway | SHORT_STRING |  | 192.168.1.1 |
| 24183 | THIRD | CM-Ethernet | Current Subnet Mask | SHORT_STRING |  | 255.255.255.0 |
| 24184 | THIRD | CM-Ethernet | Current IP Address | SHORT_STRING |  | 192.168.1.9 |
| 24202 | THIRD | IL Info | Password Decode | UNSIGNED32 |  | *** |
| 24212 | ONE_TIME | Invisible | FW Patch Version | UNSIGNED16 |  | — |
| 24213 | ONE_TIME | Invisible | FW Version | UNSIGNED16 |  | — |
| 24265 | THIRD | CM-4G-GPS | Satellites | UNSIGNED8 |  | 0 |
| 24266 | THIRD | CM-4G-GPS | Altitude | INTEGER16 | m | -32768 |
| 24267 | THIRD | CM-4G-GPS | Longitude | SHORT_STRING |  | #### |
| 24268 | THIRD | CM-4G-GPS | Latitude | SHORT_STRING |  | #### |
| 24288 | FIRST | CM-4G-GPS | Cell Diag Code | UNSIGNED8 |  | 255 |
| 24289 | FIRST | CM-RS232-485 | GSM Diag Code | UNSIGNED8 |  | 255 |
| 24290 | SECOND | CM-4G-GPS | Cell Status | SHORT_STRING |  |  |
| 24291 | SECOND | CM-RS232-485 | GSM Status | SHORT_STRING |  |  |
| 24292 | ONE_TIME | Invisible | HW Version | UNSIGNED8 |  | — |
| 24300 | THIRD | CM-4G-GPS | Cell ErrorRate | UNSIGNED8 | % | 100 |
| 24301 | THIRD | CM-RS232-485 | GSM ErrorRate | UNSIGNED8 | % | 100 |
| 24302 | THIRD | CM-4G-GPS | Cell Signal Lev | UNSIGNED8 | % | 0 |
| 24303 | THIRD | CM-RS232-485 | GSM Signal Level | UNSIGNED8 | % | 0 |
| 24307 | THIRD | CM-4G-GPS | Last E-mail Result | UNSIGNED8 |  | 29 |
| 24308 | THIRD | CM-4G-GPS | AirGate Status | UNSIGNED8 |  | 0 |
| 24309 | THIRD | CM-4G-GPS | AirGate ID | SHORT_STRING |  |  |
| 24332 | THIRD | CM-Ethernet | Last E-mail Result | UNSIGNED8 |  | 0 |
| 24333 | THIRD | CM-Ethernet | MAC Address | LONG_STRING |  | *** |
| 24339 | ONE_TIME | IL Info | FW Version | SHORT_STRING |  | — |
| 24344 | THIRD | CM-Ethernet | AirGate Status | UNSIGNED8 |  | 0 |
| 24345 | THIRD | CM-Ethernet | AirGate ID | SHORT_STRING |  |  |
| 24414 | THIRD | Invisible | Terminal Features | UNSIGNED32 |  | 127 |
| 24501 | ONE_TIME | IL Info | ID String | LONG_STRING |  | — |
| 24517 | SECOND | Invisible | Reserved | FLOAT |  | 2.369356361395559e-38 |

## Setpoints

| # | Group | Name | Type | Unit | Min | Max | Password | Value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8252 | Basic Settings | Gear Teeth | UNSIGNED16 |  | 0 | 500 | yes | 0 |
| 8253 | Basic Settings | Nominal RPM | UNSIGNED16 | RPM | 100 | 4000 | yes | 3000 |
| 8254 | Engine Settings | Starting RPM | UNSIGNED8 | % | 5 | 50 | yes | 40 |
| 8255 | Engine Settings | Cranking Attempts | UNSIGNED8 |  | 1 | 10 | yes | 7 |
| 8256 | Engine Settings | Maximum Cranking Time | UNSIGNED8 | s | 1 | 255 | yes | 10 |
| 8257 | Engine Settings | Cranking Fail Pause | UNSIGNED8 | s | 5 | 60 | yes | 15 |
| 8258 | Engine Settings | Cooling Time | UNSIGNED16 | s | 0 | 3600 | yes | 30 |
| 8259 | Engine Settings | Minimal Stabilization Time | UNSIGNED16 | s | 1 | var | yes | 2 |
| 8260 | Engine Settings | Underspeed Sd | UNSIGNED16 | % | 0 | var | no | 25 |
| 8263 | Engine Settings | Overspeed Sd | UNSIGNED16 | % | var | 150 | yes | 125 |
| 8264 | Basic Settings | Horn Timeout | UNSIGNED16 | s | 0 | 600 | yes | 10 |
| 8274 | Basic Settings | CT Ratio | UNSIGNED16 | /5A | 1 | 5000 | yes | 100 |
| 8275 | Basic Settings | Nominal Current | UNSIGNED16 | A | 1 | 10000 | yes | 63 |
| 8276 | Basic Settings | Nominal Power | UNSIGNED16 | kW | 0.1 | 500 | yes | 1.5 |
| 8277 | Basic Settings | Nominal Voltage Ph-N | UNSIGNED16 | V | 80 | 20000 | yes | 231 |
| 8278 | Basic Settings | Nominal Frequency | UNSIGNED16 | Hz | 45 | 65 | yes | 50 |
| 8280 | Generator Settings | Overload BOC | UNSIGNED16 | % | var | 200 | yes | 120 |
| 8281 | Generator Settings | Overload Delay | UNSIGNED16 | s | 0 | 600 | yes | 6 |
| 8282 | Generator Settings | Short Circuit BOC | UNSIGNED16 | % | 100 | 500 | yes | 250 |
| 8283 | Generator Settings | IDMT Overcurrent | UNSIGNED16 | s | 1 | 600 | yes | 0.4 |
| 8284 | Generator Settings | Current Unbalance BOC | UNSIGNED16 | % | 1 | 200 | yes | 50 |
| 8285 | Generator Settings | Current Unbalance BOC Delay | UNSIGNED16 | s | 0 | 600 | yes | 0.5 |
| 8288 | Generator Settings | Voltage Unbalance BOC | UNSIGNED16 | % | 1 | 200 | yes | 50 |
| 8289 | Generator Settings | Voltage Unbalance BOC Delay | UNSIGNED16 | s | 0 | 600 | yes | 0.3 |
| 8291 | Generator Settings | Generator Overvoltage Sd | UNSIGNED16 | % | var | 200 | yes | 120 |
| 8293 | Generator Settings | Generator Undervoltage BOC | UNSIGNED16 | % | 0 | var | yes | 70 |
| 8296 | Generator Settings | Generator Overfrequency BOC | UNSIGNED16 | % | var | 200 | yes | 11.5 |
| 8297 | Generator Settings | Generator <> Frequency Delay | UNSIGNED16 | s | 0 | 600 | yes | 0.3 |
| 8298 | Generator Settings | Generator Underfrequency BOC | UNSIGNED16 | % | 0 | var | yes | 8.5 |
| 8301 | AMF Settings | Emergency Start Delay | UNSIGNED16 | s | 0 | 6000 | yes | 10 |
| 8302 | AMF Settings | Mains Return Delay | UNSIGNED16 | s | 1 | 3600 | yes | 20 |
| 8303 | Dual Operation | Transfer Delay | UNSIGNED16 | s | 0 | 600 | yes | 0.1 |
| 8305 | AMF Settings | Mains Overvoltage | UNSIGNED16 | % | var | 150 | yes | 120 |
| 8306 | AMF Settings | Mains <> Voltage Delay | UNSIGNED16 | s | 0 | 600 | yes | 0.2 |
| 8307 | AMF Settings | Mains Undervoltage | UNSIGNED16 | % | 50 | var | yes | 60 |
| 8310 | AMF Settings | Mains Overfrequency | UNSIGNED16 | % | var | 150 | yes | 10.2 |
| 8311 | AMF Settings | Mains <> Frequency Delay | UNSIGNED16 | s | 0 | 600 | yes | 0.05 |
| 8312 | AMF Settings | Mains Underfrequency | UNSIGNED16 | % | 50 | var | yes | 9.8 |
| 8313 | Engine Settings | Maximal Stabilization Time | UNSIGNED16 | s | var | 300 | yes | 10 |
| 8315 | Basic Settings | Controller Mode | STRING_LIST |  | 41 | 44 | no | AUTO |
| 8383 | Engine Settings | Battery <> Voltage Delay | UNSIGNED16 | s | 0 | 600 | yes | 10 |
| 8387 | Engine Settings | Battery Undervoltage | INTEGER16 | V | 8 | var | yes | 0.8 |
| 8389 | AMF Settings | MCB Close Delay | UNSIGNED16 | s | 0 | 600 | yes | 0.1 |
| 8394 | Engine Settings | Prestart Time | UNSIGNED16 | s | 0 | 600 | yes | 10 |
| 8407 | CU AIN Calibration | CU AIN2 Calibration | INTEGER16 |  | -1000 | 1000 | no | 0 |
| 8431 | CU AIN Calibration | CU AIN1 Calibration | INTEGER16 |  | -1000 | 1000 | no | 0 |
| 8444 | AMF Settings | MCB Logic | STRING_LIST |  | 52 | 53 | yes | Close-Off |
| 8446 | AMF Settings | Mains Voltage Unbalance | UNSIGNED16 | % | 1 | 150 | yes | 10 |
| 8447 | AMF Settings | Mains Voltage Unbalance Delay | UNSIGNED16 | s | 0 | 600 | yes | 0.2 |
| 8467 | CU AIN Calibration | CU AIN3 Calibration | INTEGER16 |  | -1000 | 1000 | no | 0 |
| 8482 | CM-Ethernet | Wrn Message | STRING_LIST |  | 58 | 59 | no | ON |
| 8484 | CM-Ethernet | Sd Message | STRING_LIST |  | 61 | 62 | no | ON |
| 8548 | Basic Settings | Zero Power Mode | UNSIGNED16 | min | 0 | 360 | yes | 0 |
| 8618 | Invisible | Return From TEST | STRING_LIST |  | 65 | 66 | yes | Manual |
| 8662 | Engine Settings | After Cooling Time | UNSIGNED16 | s | 0 | 3600 | yes | 180 |
| 8688 | Engine Settings | Temperature Switch On | INTEGER16 | °C | -16 | 120 | yes | 90 |
| 8689 | Engine Settings | Temperature Switch Off | INTEGER16 | °C | -16 | 120 | yes | 75 |
| 8727 | Scheduler | Summer Time Mode | STRING_LIST |  | 72 | 76 | yes | Summer |
| 8793 | CU AIN Calibration | CU AIN4 Calibration | INTEGER16 |  | -1000 | 1000 | no | 0 |
| 8979 | Scheduler | Time Stamp Period | UNSIGNED8 | min | 0 | 240 | yes | 240 |
| 9097 | Engine Settings | Idle Time | UNSIGNED16 | s | 0 | 600 | yes | 12 |
| 9100 | Engine Settings | Fuel Solenoid | STRING_LIST |  | 81 | 82 | yes | Diesel |
| 9103 | Generator Settings | Generator <> Voltage Delay | UNSIGNED16 | s | 0 | 600 | yes | 0.5 |
| 9259 | General Analog Inputs | AIN Prot01 Wrn | INTEGER16 |  | 0 | 1000 | yes | 0 |
| 9260 | General Analog Inputs | AIN Prot01 Sd | INTEGER16 |  | 0 | 1000 | yes | 0 |
| 9261 | General Analog Inputs | AIN Prot01 Delay | UNSIGNED16 | s | 0 | 900 | yes | 0 |
| 9262 | General Analog Inputs | AIN Prot02 Wrn | INTEGER16 |  | 0 | 1000 | yes | 0 |
| 9263 | General Analog Inputs | AIN Prot02 Sd | INTEGER16 |  | 0 | 1000 | yes | 0 |
| 9264 | General Analog Inputs | AIN Prot02 Delay | UNSIGNED16 | s | 0 | 900 | yes | 0 |
| 9265 | General Analog Inputs | AIN Prot03 Wrn | INTEGER16 |  | 0 | 1000 | yes | 0 |
| 9266 | General Analog Inputs | AIN Prot03 Sd | INTEGER16 |  | 0 | 1000 | yes | 0 |
| 9267 | General Analog Inputs | AIN Prot03 Delay | UNSIGNED16 | s | 0 | 900 | yes | 0 |
| 9268 | General Analog Inputs | AIN Prot04 Wrn | INTEGER16 |  | 0 | 1000 | yes | 0 |
| 9269 | General Analog Inputs | AIN Prot04 Sd | INTEGER16 |  | 0 | 1000 | yes | 0 |
| 9270 | General Analog Inputs | AIN Prot04 Delay | UNSIGNED16 | s | 0 | 900 | yes | 0 |
| 9271 | General Analog Inputs | AIN Prot05 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9272 | General Analog Inputs | AIN Prot05 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9273 | General Analog Inputs | AIN Prot05 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9274 | General Analog Inputs | AIN Prot06 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9275 | General Analog Inputs | AIN Prot06 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9276 | General Analog Inputs | AIN Prot06 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9277 | General Analog Inputs | AIN Prot07 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9278 | General Analog Inputs | AIN Prot07 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9279 | General Analog Inputs | AIN Prot07 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9280 | General Analog Inputs | AIN Prot08 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9281 | General Analog Inputs | AIN Prot08 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9282 | General Analog Inputs | AIN Prot08 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9283 | General Analog Inputs | AIN Prot09 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9284 | General Analog Inputs | AIN Prot09 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9285 | General Analog Inputs | AIN Prot09 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9286 | General Analog Inputs | AIN Prot10 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9287 | General Analog Inputs | AIN Prot10 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9288 | General Analog Inputs | AIN Prot10 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9289 | General Analog Inputs | AIN Prot11 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9290 | General Analog Inputs | AIN Prot11 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9291 | General Analog Inputs | AIN Prot11 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9292 | General Analog Inputs | AIN Prot12 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9293 | General Analog Inputs | AIN Prot12 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9294 | General Analog Inputs | AIN Prot12 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9295 | General Analog Inputs | AIN Prot13 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9296 | General Analog Inputs | AIN Prot13 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9297 | General Analog Inputs | AIN Prot13 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9298 | General Analog Inputs | AIN Prot14 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9299 | General Analog Inputs | AIN Prot14 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9300 | General Analog Inputs | AIN Prot14 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9301 | General Analog Inputs | AIN Prot15 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9302 | General Analog Inputs | AIN Prot15 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9303 | General Analog Inputs | AIN Prot15 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9304 | General Analog Inputs | AIN Prot16 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9305 | General Analog Inputs | AIN Prot16 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9306 | General Analog Inputs | AIN Prot16 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9307 | General Analog Inputs | AIN Prot17 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9308 | General Analog Inputs | AIN Prot17 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9309 | General Analog Inputs | AIN Prot17 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9310 | General Analog Inputs | AIN Prot18 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9311 | General Analog Inputs | AIN Prot18 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9312 | General Analog Inputs | AIN Prot18 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9313 | General Analog Inputs | AIN Prot19 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9314 | General Analog Inputs | AIN Prot19 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9315 | General Analog Inputs | AIN Prot19 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9316 | General Analog Inputs | AIN Prot20 Wrn | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9317 | General Analog Inputs | AIN Prot20 Sd | INTEGER16 |  | 0 | 1000 | no | 0 |
| 9318 | General Analog Inputs | AIN Prot20 Delay | UNSIGNED16 | s | 0 | 900 | no | 0 |
| 9579 | Basic Settings | PT Ratio | UNSIGNED16 | V/V | 0.1 | 500 | yes | 0.1 |
| 9580 | Basic Settings | Vm PT Ratio | UNSIGNED16 | V/V | 0.1 | 500 | yes | 0.1 |
| 9587 | Engine Settings | Battery Overvoltage | INTEGER16 | V | var | 40 | yes | 1.7 |
| 9590 | AMF Settings | Return From Island | STRING_LIST |  | 148 | 149 | yes | Auto |
| 9681 | Engine Settings | Starting Oil Pressure | INTEGER16 | Bar | 0 | 10 | yes | 0 |
| 9683 | Engine Settings | D+ Function | STRING_LIST |  | 152 | 154 | yes | Disabled |
| 9684 | Engine Settings | Coolant Temperature Low Wrn | INTEGER16 | °C | -16 | 120 | yes | 5 |
| 9685 | Generator Settings | Overload Wrn | UNSIGNED16 | % | 0 | var | yes | 120 |
| 9686 | Generator Settings | Generator Overvoltage Wrn | UNSIGNED16 | % | var | var | yes | 115 |
| 9687 | Generator Settings | Generator Undervoltage Wrn | UNSIGNED16 | % | var | var | yes | 85 |
| 9688 | Generator Settings | Generator Overfrequency Wrn | UNSIGNED16 | % | var | var | yes | 11.5 |
| 9689 | Generator Settings | Generator Underfrequency Wrn | UNSIGNED16 | % | var | var | yes | 8.5 |
| 9695 | Engine Settings | Sd Ventilation Time | UNSIGNED16 | s | 0 | 60 | yes | 5 |
| 9815 | Engine Settings | Stop Time | UNSIGNED16 | s | 0 | 600 | yes | 10 |
| 9850 | AMF Settings | MCB Opens On | STRING_LIST |  | 164 | 165 | yes | Mains Fail |
| 9913 | Alternate Config | Nominal Frequency 1 | UNSIGNED16 | Hz | 45 | 65 | no | 50 |
| 9914 | Alternate Config | Nominal Frequency 2 | UNSIGNED16 | Hz | 45 | 65 | no | 50 |
| 9915 | Alternate Config | Nominal RPM 1 | UNSIGNED16 | RPM | 100 | 4000 | no | 3000 |
| 9916 | Alternate Config | Nominal RPM 2 | UNSIGNED16 | RPM | 100 | 4000 | no | 1500 |
| 9946 | Engine Settings | Idle RPM | UNSIGNED16 | RPM | 100 | 4000 | no | 900 |
| 9948 | Engine Settings | ECU Speed Adjustment | UNSIGNED16 | % | 0 | 100 | yes | 50 |
| 9977 | Basic Settings | Nominal Power Split Phase | UNSIGNED16 | kW | 0.1 | 500 | yes | 2 |
| 9983 | Basic Settings | Reset To Manual | STRING_LIST |  | 174 | 175 | yes | Disabled |
| 9991 | Generator Settings | Short Circuit BOC Delay | UNSIGNED16 | s | 0 | 10 | yes | 0.0004 |
| 10023 | Engine Settings | Protection Hold Off | UNSIGNED16 | s | 0 | 300 | yes | 1 |
| 10046 | Engine Settings | Cooling Speed | STRING_LIST |  | 179 | 180 | yes | Nominal |
| 10100 | Engine Settings | Fuel Pump On | INTEGER16 | % | 0 | var | yes | 20 |
| 10101 | Engine Settings | Fuel Pump Off | INTEGER16 | % | var | 100 | yes | 90 |
| 10121 | Basic Settings | Backlight Timeout | UNSIGNED8 | min | 0 | 255 | yes | 2 |
| 10270 | Engine Settings | Coolant Temperature Low Delay | UNSIGNED16 | s | 0 | 900 | yes | 5 |
| 10343 | Invisible | User Mode | UNSIGNED8 |  | 0 | 1 | no | 1 |
| 10440 | PLC | Ssanie | INTEGER16 | s | 0 | 60 | no | 0.2 |
| 10441 | PLC | Stop_puls | INTEGER16 | s | 1 | 60 | no | 1 |
| 10442 | PLC | PLC Parametr 3 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10443 | PLC | PLC Parametr 4 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10444 | PLC | PLC Parametr 5 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10445 | PLC | PLC Parametr 6 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10446 | PLC | PLC Parametr 7 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10447 | PLC | PLC Parametr 8 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10448 | PLC | PLC Parametr 9 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10449 | PLC | PLC Parametr 10 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10450 | PLC | PLC Parametr 11 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10451 | PLC | PLC Parametr 12 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10452 | PLC | PLC Parametr 13 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10453 | PLC | PLC Parametr 14 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10454 | PLC | PLC Parametr 15 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10455 | PLC | PLC Parametr 16 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10456 | PLC | PLC Parametr 17 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10457 | PLC | PLC Parametr 18 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10458 | PLC | PLC Parametr 19 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10459 | PLC | PLC Parametr 20 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10460 | PLC | PLC Parametr 21 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10461 | PLC | PLC Parametr 22 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10462 | PLC | PLC Parametr 23 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10463 | PLC | PLC Parametr 24 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10464 | PLC | PLC Parametr 25 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10465 | PLC | PLC Parametr 26 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10466 | PLC | PLC Parametr 27 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10467 | PLC | PLC Parametr 28 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10468 | PLC | PLC Parametr 29 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10469 | PLC | PLC Parametr 30 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10470 | PLC | PLC Parametr 31 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10471 | PLC | PLC Parametr 32 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10472 | PLC | PLC Parametr 33 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10473 | PLC | PLC Parametr 34 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10474 | PLC | PLC Parametr 35 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10475 | PLC | PLC Parametr 36 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10476 | PLC | PLC Parametr 37 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10477 | PLC | PLC Parametr 38 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10478 | PLC | PLC Parametr 39 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10479 | PLC | PLC Parametr 40 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10480 | PLC | PLC Parametr 41 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10481 | PLC | PLC Parametr 42 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10482 | PLC | PLC Parametr 43 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10483 | PLC | PLC Parametr 44 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10484 | PLC | PLC Parametr 45 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10485 | PLC | PLC Parametr 46 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10486 | PLC | PLC Parametr 47 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10487 | PLC | PLC Parametr 48 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10488 | PLC | PLC Parametr 49 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10489 | PLC | PLC Parametr 50 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10490 | PLC | PLC Parametr 51 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10491 | PLC | PLC Parametr 52 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10492 | PLC | PLC Parametr 53 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10493 | PLC | PLC Parametr 54 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10494 | PLC | PLC Parametr 55 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10495 | PLC | PLC Parametr 56 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10496 | PLC | PLC Parametr 57 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10497 | PLC | PLC Parametr 58 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10498 | PLC | PLC Parametr 59 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10499 | PLC | PLC Parametr 60 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10500 | PLC | PLC Parametr 61 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10501 | PLC | PLC Parametr 62 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10502 | PLC | PLC Parametr 63 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10503 | PLC | PLC Parametr 64 | INTEGER16 |  | -32768 | 32767 | no | 0 |
| 10525 | Engine Settings | Fuel Solenoid Lead | INTEGER16 | s | 0 | 25 | yes | 0.08 |
| 10566 | CM-Ethernet | BOC Message | STRING_LIST |  | 252 | 253 | no | ON |
| 10685 | Engine Settings | Transfer Wrn Delay | UNSIGNED16 | s | 0 | 60 | yes | 30 |
| 10926 | CM-Ethernet | Event Message | STRING_LIST |  | 256 | 257 | no | ON |
| 10994 | Engine Settings | Conversion Coefficient Pulse 1 | UNSIGNED16 |   | 0 | 1000 | no | 1 |
| 10995 | Engine Settings | Conversion Coefficient Pulse 2 | UNSIGNED16 |   | 0 | 1000 | no | 1 |
| 11103 | Engine Settings | Fuel Tank Volume | UNSIGNED16 | L | 0 | 10000 | yes | 0 |
| 11374 | Engine Settings | Battery Charger Fail Delay | UNSIGNED8 | min | 0 | 15 | yes | 5 |
| 11407 | General Analog Inputs | AIN Switch01 On | INTEGER16 |  | 0 | 32000 | yes | 0 |
| 11408 | General Analog Inputs | AIN Switch02 On | INTEGER16 |  | 0 | 32000 | yes | 0 |
| 11409 | General Analog Inputs | AIN Switch03 On | INTEGER16 |  | 0 | 32000 | yes | 0 |
| 11410 | General Analog Inputs | AIN Switch01 Off | INTEGER16 |  | 0 | 32000 | yes | 0 |
| 11411 | General Analog Inputs | AIN Switch02 Off | INTEGER16 |  | 0 | 32000 | yes | 0 |
| 11412 | General Analog Inputs | AIN Switch03 Off | INTEGER16 |  | 0 | 32000 | yes | 0 |
| 11616 | Statistics | Maintenance Timer 1 | INTEGER16 | h | -10000 | 10000 | no | 5 |
| 11617 | Statistics | Maintenance Timer 2 | INTEGER16 | h | -10000 | 10000 | no | 10000 |
| 11618 | Statistics | Maintenance Timer 3 | INTEGER16 | h | -10000 | 10000 | no | 10000 |
| 11625 | Basic Settings | CT Location | STRING_LIST |  | 271 | 273 | yes | GenSet |
| 11628 | Basic Settings | Connection Type | STRING_LIST |  | 275 | 281 | yes | MonoPhase |
| 11631 | EM-BIO8-EFCP | Earth Fault Current Protection | STRING_LIST |  | 283 | 284 | no | Enabled |
| 11632 | EM-BIO8-EFCP | Earth Fault Sd | UNSIGNED16 | A | 0.03 | 5 | no | 0.003 |
| 11633 | EM-BIO8-EFCP | Earth Fault Delay | UNSIGNED16 | s | 0.03 | 5 | no | 0.001 |
| 11657 | Basic Settings | Nominal Voltage Ph-Ph | UNSIGNED16 | V | 80 | 40000 | yes | 231 |
| 11658 | Engine Settings | Power Switch On | INTEGER16 | kW | 0 | 3200 | yes | 1 |
| 11659 | Engine Settings | Power Switch Off | INTEGER16 | kW | 0 | 3200 | yes | 0.5 |
| 11677 | Geo-Fencing | Fence Radius 1 | UNSIGNED16 | km | 0 | 99.9 | yes | 0 |
| 11681 | Geo-Fencing | Geo-Fencing | STRING_LIST |  | 292 | 294 | yes | Disable |
| 11682 | Geo-Fencing | Fence 1 Delay | UNSIGNED16 | s | 0 | 3600 | yes | 0 |
| 12046 | Alternate Config | Nominal Power 1 | UNSIGNED16 | kW | 0.1 | 500 | no | 1.5 |
| 12047 | Alternate Config | Nominal Power 2 | UNSIGNED16 | kW | 0.1 | 500 | no | 2 |
| 12048 | Alternate Config | Nominal Power 3 | UNSIGNED16 | kW | 0.1 | 500 | no | 2 |
| 12049 | Alternate Config | Nominal Current 1 | UNSIGNED16 | A | 1 | 10000 | no | 63 |
| 12050 | Alternate Config | Nominal Current 2 | UNSIGNED16 | A | 1 | 10000 | no | 50 |
| 12051 | Alternate Config | Nominal Current 3 | UNSIGNED16 | A | 1 | 10000 | no | 350 |
| 12052 | Alternate Config | Nominal Voltage Ph-N 1 | UNSIGNED16 | V | 80 | 20000 | no | 231 |
| 12053 | Alternate Config | Nominal Voltage Ph-N 2 | UNSIGNED16 | V | 80 | 20000 | no | 231 |
| 12054 | Alternate Config | Nominal Voltage Ph-N 3 | UNSIGNED16 | V | 80 | 20000 | no | 231 |
| 12055 | Alternate Config | Nominal Voltage Ph-Ph 1 | UNSIGNED16 | V | 80 | 40000 | no | 231 |
| 12056 | Alternate Config | Nominal Voltage Ph-Ph 2 | UNSIGNED16 | V | 80 | 40000 | no | 400 |
| 12057 | Alternate Config | Nominal Voltage Ph-Ph 3 | UNSIGNED16 | V | 80 | 40000 | no | 400 |
| 12058 | Alternate Config | Connection Type 1 | STRING_LIST |  | 309 | 315 | no | MonoPhase |
| 12059 | Alternate Config | Connection Type 2 | STRING_LIST |  | 317 | 323 | no | 3Ph4Wire |
| 12060 | Alternate Config | Connection Type 3 | STRING_LIST |  | 325 | 331 | no | 3Ph4Wire |
| 12157 | Basic Settings | Operation Mode | STRING_LIST |  | 333 | 334 | yes | AMF |
| 12373 | Engine Settings | Maximal Fuel Drop | UNSIGNED8 | %/h | 0 | 50 | yes | 0 |
| 12779 | Engine Settings | Oil Pressure Sd | INTEGER16 | Bar | 0 | 10 | yes | 0.1 |
| 12780 | Engine Settings | Coolant Temperature BOC | INTEGER16 | °C | -16 | 120 | yes | 90 |
| 12895 | Engine Settings | Oil Pressure Wrn | INTEGER16 | Bar | 0 | 10 | yes | 0.2 |
| 12896 | Engine Settings | Coolant Temperature Wrn | INTEGER16 | °C | -16 | 120 | yes | 80 |
| 12897 | Engine Settings | Fuel Level Wrn | INTEGER16 | % | 0 | 100 | yes | 20 |
| 12898 | Engine Settings | Fuel Level BOC | INTEGER16 | % | 0 | 100 | yes | 10 |
| 13000 | Basic Settings | Power On Mode | STRING_LIST |  | 343 | 344 | no | Previous |
| 13011 | Engine Settings | Choke Time | UNSIGNED16 | s | 0 | 3600 | no | 5 |
| 13345 | Basic Settings | RunHoursSource | STRING_LIST |  | 347 | 349 | no | AUTO |
| 13346 | Basic Settings | Main Screen Line 1 | STRING_LIST |  | 351 | 355 | yes | RPM |
| 14107 | Engine Settings | Overspeed Overshoot | UNSIGNED8 | % | 0 | 50 | yes | 20 |
| 14108 | Engine Settings | Overspeed Overshoot Period | UNSIGNED8 | s | 0 | 255 | yes | 5 |
| 14326 | Scheduler | Rental Timer 1 | UNSIGNED16 | h | 0 | 8760 | yes | 0 |
| 14332 | Scheduler | Rental Timer 1 Wrn | UNSIGNED16 | h | 0 | var | yes | 0 |
| 14334 | Scheduler | Rental Timer BOC | UNSIGNED16 | h | 0 | 210 | yes | 24 |
| 14337 | Alternate Config | ECU Speed Adjustment 1 | UNSIGNED16 | % | 0 | 100 | no | 50 |
| 14338 | Alternate Config | ECU Speed Adjustment 2 | UNSIGNED16 | % | 0 | 100 | no | 50 |
| 14339 | EM-BIO8-EFCP | Earth Fault CT Ratio | UNSIGNED16 | /(1or5)A | 1 | 2000 | no | 500 |
| 14340 | EM-BIO8-EFCP | Earth Fault CT Input Range | STRING_LIST |  | 365 | 366 | no | 5A |
| 14341 | Engine Settings | Oil Pressure Delay | UNSIGNED16 | s | 0 | 900 | yes | 6 |
| 14342 | Engine Settings | Coolant Temperature Delay | UNSIGNED16 | s | 0 | 900 | yes | 5 |
| 14343 | Engine Settings | Fuel Level Delay | UNSIGNED16 | s | 0 | 900 | yes | 10 |
| 14385 | General Analog Inputs | AIN Switch04 On | INTEGER16 |  | 0 | 32000 | yes | 0 |
| 14386 | General Analog Inputs | AIN Switch04 Off | INTEGER16 |  | 0 | 32000 | yes | 0 |
| 14412 | Engine Settings | Glow Plugs Time | UNSIGNED16 | s | 0 | var | yes | 0 |
| 14425 | Engine Settings | ECU Oil Pressure Sd | INTEGER16 | Bar | 0 | 10 | yes | 0.1 |
| 14426 | Engine Settings | ECU Oil Pressure Wrn | INTEGER16 | Bar | 0 | 10 | yes | 0.2 |
| 14427 | Engine Settings | ECU Oil Pressure Delay | UNSIGNED16 | s | 0 | 900 | yes | 3 |
| 14428 | Engine Settings | ECU Coolant Temperature BOC | INTEGER16 | °C | -50 | 500 | yes | 90 |
| 14429 | Engine Settings | ECU Coolant Temperature Wrn | INTEGER16 | °C | -50 | 500 | yes | 80 |
| 14430 | Engine Settings | ECU Coolant Temperature Delay | UNSIGNED16 | s | 0 | 900 | yes | 5 |
| 14431 | Engine Settings | ECU Fuel Level BOC | INTEGER16 | % | 0 | 100 | yes | 10 |
| 14432 | Engine Settings | ECU Fuel Level Wrn | INTEGER16 | % | 0 | 100 | yes | 20 |
| 14433 | Engine Settings | ECU Fuel Level Delay | UNSIGNED16 | s | 0 | 900 | yes | 10 |
| 14606 | Geo-Fencing | Home Latitude | INTEGER32 |  | -0.09 | 0.09 | yes | 0 |
| 14607 | Geo-Fencing | Home Longitude | INTEGER32 |  | -0.18 | 0.18 | yes | 0 |
| 14608 | Geo-Fencing | Fence Radius 2 | UNSIGNED16 | km | 0 | 99.9 | yes | 0 |
| 14609 | Geo-Fencing | Fence 2 Delay | UNSIGNED16 | s | 0 | 3600 | yes | 0 |
| 14610 | Geo-Fencing | Fence 1 Protection | STRING_LIST |  | 389 | 392 | yes | HistRecOnl |
| 14611 | Geo-Fencing | Fence 2 Protection | STRING_LIST |  | 394 | 397 | yes | HistRecOnl |
| 14628 | Basic Settings | Main Screen Line 2 | STRING_LIST |  | 399 | 403 | no | Run Hours |
| 14683 | Engine Settings | Maximal Fuel Drop Delay | UNSIGNED16 | s | 0 | 600 | yes | 5 |
| 14959 | Engine Settings | D+ Threshold | UNSIGNED8 | % | 0 | 100 | no | 80 |
| 14960 | Engine Settings | D+ Delay | UNSIGNED8 | s | 1 | 255 | no | 1 |
| 14963 | General Analog Inputs | AIN Switch05 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14964 | General Analog Inputs | AIN Switch06 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14965 | General Analog Inputs | AIN Switch07 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14966 | General Analog Inputs | AIN Switch08 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14967 | General Analog Inputs | AIN Switch09 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14968 | General Analog Inputs | AIN Switch10 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14969 | General Analog Inputs | AIN Switch11 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14970 | General Analog Inputs | AIN Switch12 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14971 | General Analog Inputs | AIN Switch13 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14972 | General Analog Inputs | AIN Switch14 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14973 | General Analog Inputs | AIN Switch15 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14974 | General Analog Inputs | AIN Switch16 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14975 | General Analog Inputs | AIN Switch17 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14976 | General Analog Inputs | AIN Switch18 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14977 | General Analog Inputs | AIN Switch19 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14978 | General Analog Inputs | AIN Switch20 On | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14979 | General Analog Inputs | AIN Switch05 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14980 | General Analog Inputs | AIN Switch06 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14981 | General Analog Inputs | AIN Switch07 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14982 | General Analog Inputs | AIN Switch08 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14983 | General Analog Inputs | AIN Switch09 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14984 | General Analog Inputs | AIN Switch10 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14985 | General Analog Inputs | AIN Switch11 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14986 | General Analog Inputs | AIN Switch12 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14987 | General Analog Inputs | AIN Switch13 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14988 | General Analog Inputs | AIN Switch14 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14989 | General Analog Inputs | AIN Switch15 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14990 | General Analog Inputs | AIN Switch16 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14991 | General Analog Inputs | AIN Switch17 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14992 | General Analog Inputs | AIN Switch18 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14993 | General Analog Inputs | AIN Switch19 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 14994 | General Analog Inputs | AIN Switch20 Off | INTEGER16 |  | 0 | 32000 | no | 0 |
| 15196 | Alternate Config | Nominal RPM 3 | UNSIGNED16 | RPM | 100 | 4000 | no | 1500 |
| 15197 | Alternate Config | Nominal Frequency 3 | UNSIGNED16 | Hz | 45 | 65 | no | 50 |
| 15199 | Alternate Config | ECU Speed Adjustment 3 | UNSIGNED16 | % | 0 | 100 | no | 50 |
| 15358 | Scheduler | Timer 1 Function | STRING_LIST |  | 443 | 448 | no | Mode OFF |
| 15359 | Scheduler | Timer 2 Function | STRING_LIST |  | 450 | 455 | no | Disable |
| 15664 | Protections | Overload Protection | STRING_LIST |  | 457 | 459 | no | Enabled |
| 15665 | Protections | Short Circuit Protection | STRING_LIST |  | 461 | 463 | no | Enabled |
| 15666 | Protections | IDMT Overcurrent Protection | STRING_LIST |  | 465 | 467 | no | Enabled |
| 15667 | Protections | Current Unbalance Protection | STRING_LIST |  | 469 | 471 | no | Enabled |
| 15668 | Protections | Generator <> Voltage Protection | STRING_LIST |  | 473 | 475 | no | Enabled |
| 15669 | Protections | Voltage Unbalance Protection | STRING_LIST |  | 477 | 479 | no | Enabled |
| 15670 | Protections | Generator Frequency Protection | STRING_LIST |  | 481 | 483 | no | Enabled |
| 15671 | Protections | Underspeed Protection | STRING_LIST |  | 485 | 487 | no | Enabled |
| 15672 | Protections | Overspeed Protection | STRING_LIST |  | 489 | 491 | no | Enabled |
| 15715 | Engine Settings | Choke Increment | UNSIGNED16 | s/°C | 0 | 20 | no | 0 |
| 15716 | Engine Settings | Choke Start Temp | INTEGER16 | °C | -20 | 80 | no | 0 |
| 15717 | Engine Settings | Choke Function | STRING_LIST |  | 495 | 497 | yes | Fixed Time |
| 15718 | Engine Settings | Choke Voltage | UNSIGNED16 | % | 0 | 100 | no | 0 |
| 15751 | Engine Settings | D+ Alarm Type | STRING_LIST |  | 500 | 502 | no | Wrn |
| 15767 | Engine Settings | Ventilation Pulse Time | UNSIGNED16 | s | 0 | 3600 | no | 30 |
| 15771 | Alternate Config | Nominal Power Split Phase 1 | UNSIGNED16 | kW | 0.1 | 500 | no | 2 |
| 15772 | Alternate Config | Nominal Power Split Phase 2 | UNSIGNED16 | kW | 0.1 | 500 | no | 2 |
| 15773 | Alternate Config | Nominal Power Split Phase 3 | UNSIGNED16 | kW | 0.1 | 500 | no | 2 |
| 15774 | Engine Settings | Choke Lead | UNSIGNED16 | s | 0 | var | no | 0 |
| 15889 | Basic Settings | Screen Filter | STRING_LIST |  | 509 | 510 | no | Disabled |
| 15890 | Invisible | Screen Filter Tau | UNSIGNED16 | ms | 100 | 10000 | no | 200 |
| 16039 | Dual Operation | Running Hours Max Difference | UNSIGNED16 | h | 0.1 | 1000 | no | 1 |
| 16040 | Dual Operation | Running Hours Base | INTEGER32 | h | -10 | 10 | no | 0 |
| 16041 | Dual Operation | Swap Gen-sets | STRING_LIST |  | 515 | 516 | no | Enabled |
| 16042 | Dual Operation | Master Error Protection | STRING_LIST |  | 518 | 520 | no | AL Indic |
| 16043 | Dual Operation | Slave Error Protection | STRING_LIST |  | 522 | 524 | no | AL Indic |
| 24110 | CM-Ethernet | Web Interface | STRING_LIST |  | 526 | 527 | no | Enabled |
| 24132 | CM-4G-GPS | Required Connection Type | STRING_LIST |  | 529 | 532 | no | Automatic |
| 24136 | CM-Ethernet | SNMP Trap Format | STRING_LIST |  | 534 | 536 | no | SNMPv1 Trap |
| 24259 | CM-Ethernet | IP Address Mode | STRING_LIST |  | 542 | 543 | no | Automatic |
| 24273 | CM-4G-GPS | AirGate Connection | STRING_LIST |  | 545 | 546 | no | Enabled |
| 24279 | Plug-In Modules | Slot B | STRING_LIST |  | 548 | 549 | yes | Disable |
| 24280 | Plug-In Modules | Slot A | STRING_LIST |  | 551 | 552 | yes | Enable |
| 24299 | CM-Ethernet | Message Language | STRING_LIST |  | 1674 | 1674 | no | English |
| 24315 | CM-4G-GPS | Internet Connection | STRING_LIST |  | 566 | 567 | no | Enabled |
| 24336 | CM-Ethernet | SNMP Agent | STRING_LIST |  | 572 | 573 | no | Enabled |
| 24337 | CM-Ethernet | MODBUS Server | STRING_LIST |  | 575 | 576 | no | Enabled |
| 24340 | CM-RS232-485 | COM 2 Communication Speed | STRING_LIST |  | 578 | 582 | yes | 57600 |
| 24341 | CM-RS232-485 | COM 1 Communication Speed | STRING_LIST |  | 584 | 588 | yes | 57600 |
| 24365 | CM-Ethernet | AirGate Connection | STRING_LIST |  | 595 | 596 | no | Disabled |
| 24366 | CM-Ethernet | Time Zone | STRING_LIST |  | 598 | 630 | no | GMT+2:00 |
| 24374 | CM-Ethernet | ComAp TCP Port | UNSIGNED16 |  | 0 | 65535 | no | 23 |
| 24420 | CM-RS232-485 | COM 2 MODBUS Communication Speed | STRING_LIST |  | 640 | 644 | yes | 9600 |
| 24451 | CM-RS232-485 | COM 2 Mode | STRING_LIST |  | 646 | 649 | yes | Direct |
| 24477 | CM-RS232-485 | COM 1 MODBUS Communication Speed | STRING_LIST |  | 651 | 655 | yes | 9600 |
| 24488 | Invisible | HMI Languague | UNSIGNED32 |  | 0 | 0 | no | 1033 |
| 24522 | CM-RS232-485 | COM 1 Mode | STRING_LIST |  | 658 | 661 | yes | Direct |
| 24537 | Basic Settings | Controller Address | UNSIGNED8 |  | 1 | 32 | yes | 1 |
