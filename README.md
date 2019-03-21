# elf_diff - A Tool to compare elf binaries

## Usage

```
elf_diff 
   <--old old_binary_file> 
   <--new binary_file>
   [--bin-dir binary_directory]
   [--bin-prefix binary_prefix]
   [--text-file text_output_file]
   [--html-file html_output_file]
```

* old_binary_file: The first input elf binary (considered to be the old state)
* new_binary_file: The second input elf binary (considered to be the new state)
* binary_directory: A directory where binutils executables can be found (defaults to `/usr/bin`)
* binary_prefix: A prefix that is added to all binutils executables (e.g. `avr-`)
* text_file: If defined, text output is redirected to this file
* html_file: If defined, only html is generated and written to this file

## Requirements

The following Python packages are required to run elf_diff:

* argparse
* difflib
* re
* jinja2, inspect (only if html output is requested)

## Example Output
```
ELF binary comparison

   (c) 2019 by noseglasses (shinynoseglasses@gmail.com)

Comparing binaries
   old: /tmp/kaleidoscope-noseglasses/sketch/17810223-Model01-Firmware.ino/output/Model01-Firmware-0.0.0.elf
   new: /tmp/kaleidoscope-noseglasses/sketch/18182958-Model01-Firmware.ino/output/Model01-Firmware-0.0.0.elf

Binary size:
   overall: 26216 -> 26306 bytes (+90 bytes) 
   text: 25960 -> 26038 bytes (+78 bytes) 
   data: 256 -> 268 bytes (+12 bytes) 

Static RAM consumption:
   overall: 1434 -> 1390 bytes (-44 bytes) *
   data: 256 -> 268 bytes (+12 bytes) 
   bss: 1178 -> 1122 bytes (-56 bytes) *

text: code instructions
data: initilized global or static variables
bss: uninitialized global or static variables

589 symbols found in /tmp/kaleidoscope-noseglasses/sketch/17810223-Model01-Firmware.ino/output/Model01-Firmware-0.0.0.elf
598 symbols found in /tmp/kaleidoscope-noseglasses/sketch/18182958-Model01-Firmware.ino/output/Model01-Firmware-0.0.0.elf

24 Symbols changed size:
   LEDBreatheEffect: 6 -> 4 bytes
   _GLOBAL__sub_I__ZN12kaleidoscope6plugin14ColormapEffect9map_base_E: 14 -> 10 bytes
   kaleidoscope::Hooks::onSetup(): 4 -> 102 bytes
   kaleidoscope::plugin::BootGreetingEffect::afterEachCycle(): 170 -> 182 bytes
   kaleidoscope::plugin::ColormapEffect::onLayerChange(): 40 -> 44 bytes
   kaleidoscope::plugin::LEDControl::activate(kaleidoscope::plugin::LEDMode*): 30 -> 72 bytes
   kaleidoscope::plugin::LEDControl::beforeReportingState(): 116 -> 102 bytes
   kaleidoscope::plugin::LEDControl::get_mode(): 20 -> 8 bytes
   kaleidoscope::plugin::LEDControl::next_mode(): 56 -> 26 bytes
   kaleidoscope::plugin::LEDControl::onSetup(): 82 -> 90 bytes
   kaleidoscope::plugin::LEDControl::prev_mode(): 54 -> 36 bytes
   kaleidoscope::plugin::LEDControl::refreshAll(): 54 -> 40 bytes
   kaleidoscope::plugin::LEDControl::set_mode(unsigned char): 22 -> 54 bytes
   kaleidoscope::plugin::LEDMode::onSetup(): 34 -> 20 bytes
   kaleidoscope::plugin::LEDSolidColor::LEDSolidColor(unsigned char, unsigned char, unsigned char): 18 -> 10 bytes
   kaleidoscope::plugin::NumPad::setKeyboardLEDColors(): 290 -> 276 bytes
   solidBlue: 5 -> 3 bytes
   solidGreen: 5 -> 3 bytes
   solidIndigo: 5 -> 3 bytes
   solidOrange: 5 -> 3 bytes
   solidRed: 5 -> 3 bytes
   solidViolet: 5 -> 3 bytes
   solidYellow: 5 -> 3 bytes
   toggleLedsOnSuspendResume(kaleidoscope::plugin::HostPowerManagement::Event): 84 -> 68 bytes

15 symbols dissappeared (527 bytes, see details below):
   _GLOBAL__sub_I__ZN12kaleidoscope6plugin10LEDControl5modesE: 8 bytes
   _GLOBAL__sub_I__ZN12kaleidoscope6plugin16LEDBreatheEffect6updateEv: 26 bytes
   kaleidoscope::EventHandlerResult kaleidoscope_internal::EventDispatcher::apply<kaleidoscope_internal::EventHandler_onSetup>(): 166 bytes
   kaleidoscope::plugin::ColormapEffect::onActivate(): 30 bytes
   kaleidoscope::plugin::ColormapEffect::refreshAt(unsigned char, unsigned char): 32 bytes
   kaleidoscope::plugin::LEDBreatheEffect::update(): 46 bytes
   kaleidoscope::plugin::LEDControl::LEDControl(): 20 bytes
   kaleidoscope::plugin::LEDControl::mode: 1 bytes
   kaleidoscope::plugin::LEDControl::mode_add(kaleidoscope::plugin::LEDMode*): 48 bytes
   kaleidoscope::plugin::LEDControl::modes: 48 bytes
   kaleidoscope::plugin::LEDControl::refreshAll() [clone .part.2]: 48 bytes
   kaleidoscope::plugin::LEDSolidColor::onActivate(): 12 bytes
   kaleidoscope::plugin::LEDSolidColor::refreshAt(unsigned char, unsigned char): 18 bytes
   vtable for kaleidoscope::plugin::ColormapEffect: 12 bytes
   vtable for kaleidoscope::plugin::LEDSolidColor: 12 bytes

24 new symbols (527 bytes, see details below):
   _GLOBAL__sub_I__ZN12kaleidoscope6plugin10LEDControl7mode_idE: 6 bytes
   _GLOBAL__sub_I__ZN12kaleidoscope6plugin16LEDBreatheEffect15ExportedLEDMode6updateEv: 22 bytes
   kaleidoscope::internal::led_mode_management::array: 37 bytes
   kaleidoscope::internal::led_mode_management::cur_led_mode: 2 bytes
   kaleidoscope::internal::led_mode_management::cur_mode_id: 1 bytes
   kaleidoscope::internal::led_mode_management::getLEDMode(unsigned char): 106 bytes
   kaleidoscope::internal::led_mode_management::led_mode_buffer: 6 bytes
   kaleidoscope::internal::led_mode_management::retreiveLEDModeFactoryFromPROGMEM(unsigned char, kaleidoscope::internal::led_mode_management::LEDModeFactory&): 26 bytes
   kaleidoscope::internal::typed_plugins::LEDMode::array: 15 bytes
   kaleidoscope::internal::typed_plugins::LEDMode::getLEDMode(unsigned char): 18 bytes
   kaleidoscope::internal::typed_plugins::LEDMode::num_entries: 1 bytes
   kaleidoscope::plugin::ColormapEffect::ExportedLEDMode::onActivate(): 30 bytes
   kaleidoscope::plugin::ColormapEffect::ExportedLEDMode::refreshAt(unsigned char, unsigned char): 32 bytes
   kaleidoscope::plugin::LEDBreatheEffect::ExportedLEDMode::update(): 52 bytes
   kaleidoscope::plugin::LEDControl::mode_id: 1 bytes
   kaleidoscope::plugin::LEDMode* kaleidoscope::internal::led_mode_management::generateLEDMode<kaleidoscope::plugin::ColormapEffect, kaleidoscope::plugin::ColormapEffect::ExportedLEDMode>(void*, void*): 26 bytes
   kaleidoscope::plugin::LEDMode* kaleidoscope::internal::led_mode_management::generateLEDMode<kaleidoscope::plugin::LEDBreatheEffect, kaleidoscope::plugin::LEDBreatheEffect::ExportedLEDMode>(void*, void*): 24 bytes
   kaleidoscope::plugin::LEDMode* kaleidoscope::internal::led_mode_management::generateLEDMode<kaleidoscope::plugin::LEDSolidColor, kaleidoscope::plugin::LEDSolidColor::ExportedLEDMode>(void*, void*): 20 bytes
   kaleidoscope::plugin::LEDSolidColor::ExportedLEDMode::onActivate(): 20 bytes
   kaleidoscope::plugin::LEDSolidColor::ExportedLEDMode::refreshAt(unsigned char, unsigned char): 28 bytes
   memcpy_P: 18 bytes
   vtable for kaleidoscope::plugin::ColormapEffect::ExportedLEDMode: 12 bytes
   vtable for kaleidoscope::plugin::LEDBreatheEffect::ExportedLEDMode: 12 bytes
   vtable for kaleidoscope::plugin::LEDSolidColor::ExportedLEDMode: 12 bytes

########################################################################
Details follow
########################################################################
The following 340 symbols' assembly differs

******************************************************************
.do_clear_bss_start (size unchanged)
******************************************************************
   - aa 39       	cpi	r26, 0x9A	; 154
   ?  ^  ^                   ^^    ^^

   + ae 36       	cpi	r26, 0x6E	; 110
   ?  ^  ^                   ^^    ^^

     b2 07       	cpc	r27, r18
   - e1 f7       	brne	.-8      	; 0x740 <.do_clear_bss_loop>
   ?                                   -

   + e1 f7       	brne	.-8      	; 0x774 <.do_clear_bss_loop>
   ?                                  +


******************************************************************
AbsoluteMouseAPI::moveTo(unsigned int, unsigned int, signed char) (size unchanged)
******************************************************************
     cf 93       	push	r28
     df 93       	push	r29
   - 00 d0       	rcall	.+0      	; 0x3de6 <AbsoluteMouseAPI::moveTo(unsigned int, unsigned int, signed char)+0x6>
   ?                                   - ^

   + 00 d0       	rcall	.+0      	; 0x3e22 <AbsoluteMouseAPI::moveTo(unsigned int, unsigned int, signed char)+0x6>
   ?                                    ^^

   - 00 d0       	rcall	.+0      	; 0x3de8 <AbsoluteMouseAPI::moveTo(unsigned int, unsigned int, signed char)+0x8>
   ?                                   - ^

   + 00 d0       	rcall	.+0      	; 0x3e24 <AbsoluteMouseAPI::moveTo(unsigned int, unsigned int, signed char)+0x8>
   ?                                    ^^

   - 00 d0       	rcall	.+0      	; 0x3dea <AbsoluteMouseAPI::moveTo(unsigned int, unsigned int, signed char)+0xa>
   ?                                   - ^

   + 00 d0       	rcall	.+0      	; 0x3e26 <AbsoluteMouseAPI::moveTo(unsigned int, unsigned int, signed char)+0xa>
   ?                                    ^^

     cd b7       	in	r28, 0x3d	; 61
     de b7       	in	r29, 0x3e	; 62
     dc 01       	movw	r26, r24
     13 96       	adiw	r26, 0x03	; 3
     7c 93       	st	X, r23
     6e 93       	st	-X, r22
     12 97       	sbiw	r26, 0x02	; 2
     15 96       	adiw	r26, 0x05	; 5
     5c 93       	st	X, r21
     4e 93       	st	-X, r20
     14 97       	sbiw	r26, 0x04	; 4
     16 96       	adiw	r26, 0x06	; 6
     3c 91       	ld	r19, X
     16 97       	sbiw	r26, 0x06	; 6
     39 83       	std	Y+1, r19	; 0x01
     7b 83       	std	Y+3, r23	; 0x03
     6a 83       	std	Y+2, r22	; 0x02
     5d 83       	std	Y+5, r21	; 0x05
     4c 83       	std	Y+4, r20	; 0x04
     2e 83       	std	Y+6, r18	; 0x06
     ed 91       	ld	r30, X+
     fc 91       	ld	r31, X
     01 90       	ld	r0, Z+
     f0 81       	ld	r31, Z
     e0 2d       	mov	r30, r0
     46 e0       	ldi	r20, 0x06	; 6
     50 e0       	ldi	r21, 0x00	; 0
     be 01       	movw	r22, r28
     6f 5f       	subi	r22, 0xFF	; 255
     7f 4f       	sbci	r23, 0xFF	; 255
     09 95       	icall
     26 96       	adiw	r28, 0x06	; 6
     0f b6       	in	r0, 0x3f	; 63
     f8 94       	cli
     de bf       	out	0x3e, r29	; 62
     0f be       	out	0x3f, r0	; 63
     cd bf       	out	0x3d, r28	; 61
     df 91       	pop	r29
     cf 91       	pop	r28
     08 95       	ret
```
