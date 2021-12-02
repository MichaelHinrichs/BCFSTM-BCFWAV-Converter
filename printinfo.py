#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BCFSTM-BCFWAV Converter
# Version v2.1
# Copyright © 2017-2018 AboodXD

# This file is part of BCFSTM-BCFWAV Converter.

#  is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BCFSTM-BCFWAV Converter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import time

from bytes import bytes_to_string
from structs import struct, Header, BLKHeader, STMInfo
from structs import TRKInfo, DSPContext, IMAContext, Ref


def readFile(f):
    pos = 0

    if f[4:6] == b'\xFF\xFE':
        bom = '<'

    elif f[4:6] == b'\xFE\xFF':
        bom = '>'

    else:
        print("Invalid BOM!")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    header = Header(bom)
    header.data(f, pos)

    if bytes_to_string(header.magic) not in ["FSTM", "CSTM", "FSTP"]:
        print("Unsupported file format!")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    print(f"Magic: {bytes_to_string(header.magic)}")
    print(f"Header size: {hex(header.size_)}")
    print(f"File version: {hex(header.version)}")
    print(f"File size: {hex(header.fileSize)}")
    print(f"Number of blocks: {str(header.numBlocks)}")

    pos += header.size
    sized_refs = {}

    for i in range(1, header.numBlocks + 1):
        sized_refs[i] = Ref(bom)
        sized_refs[i].data(f, pos + 12 * (i - 1))
        sized_refs[i].block_size = struct.unpack(f"{bom}I", f[pos + 12 * (i - 1) + 8:pos + 12 * i])[0]

        if sized_refs[i].offset not in [0, -1]:
            if sized_refs[i].type_ == 0x4000:
                print(f"\nInfo Block offset: {hex(sized_refs[i].offset)}")

            elif sized_refs[i].type_ == 0x4001:
                print(f"\nSeek Block offset: {hex(sized_refs[i].offset)}")

            elif sized_refs[i].type_ == 0x4002:
                print(f"\nData Block offset: {hex(sized_refs[i].offset)}")

            elif sized_refs[i].type_ == 0x4004:
                print(f"\nPrefetch Data Block offset: {hex(sized_refs[i].offset)}")

            else:
                print(f"\n" {hex(sized_refs[i].type_)} Block offset: {hex(sized_refs[i].offset)}")

            print(f"Size: {hex(sized_refs[i].block_size)}")

    if sized_refs[1].type_ != 0x4000 or sized_refs[1].offset in [0, -1]:
        print("\nSomething went wrong!\nError code: 1")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos = sized_refs[1].offset

    info = BLKHeader(bom)
    info.data(f, pos)

    print(f"\nInfo Block Magic: {bytes_to_string(info.magic)}")
    print(f"Size: {hex(info.size_)}")

    pos += info.size

    stmInfo_ref = Ref(bom)
    stmInfo_ref.data(f, pos)

    if stmInfo_ref.type_ != 0x4100 or stmInfo_ref.offset in [0, -1]:
        print("\nSomething went wrong!\nError code: 2")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    print(f"\nStream Info offset: {hex(stmInfo_ref.offset + pos)}")

    stmInfo_ref.pos = pos
    pos += stmInfo_ref.size

    trkInfoTable_ref = Ref(bom)
    trkInfoTable_ref.data(f, pos)

    if trkInfoTable_ref.offset not in [0, -1] and trkInfoTable_ref.type_ == 0x0101:
        print(f"\nTrack Info Reference Table offset: {hex(trkInfoTable_ref.offset + stmInfo_ref.pos)}")

    elif not trkInfoTable_ref.type_ or trkInfoTable_ref.offset in [0, -1]:
        pass

    else:
        print("\nSomething went wrong!\nError code: 3")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos += trkInfoTable_ref.size

    channelInfoTable_ref = Ref(bom)
    channelInfoTable_ref.data(f, pos)

    if channelInfoTable_ref.type_ != 0x0101:
        print("\nSomething went wrong!\nError code: 4")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    if channelInfoTable_ref.offset not in [0, -1]:
        print(f"\nChannel Info Reference Table offset: {hex(channelInfoTable_ref.offset + stmInfo_ref.pos)}")

    pos = stmInfo_ref.offset + stmInfo_ref.pos
    stmInfo = STMInfo(bom)
    stmInfo.data(f, pos)

    codec = {0: "PCM8", 1: "PCM16", 2: "DSP ADPCM", 3: "IMA ADPCM"}
    if stmInfo.codec in codec:
        print(f"\nEncoding: {codec[stmInfo.codec]}")

    else:
        print(f"\nEncoding: {str(stmInfo.codec)}")

    print(f"Loop Flag: {str(stmInfo.loop_flag)}")
    print(f"Channel Count: {str(stmInfo.count)}")
    print(f"Sample Rate: {str(stmInfo.sample)}")
    print(f"Loop Start Frame: {str(stmInfo.loop_start)}")
    print(f"Loop End Frame: {str(stmInfo.loop_end)}")
    print(f"Sample Block Count: {str(stmInfo.sampleBlk_count)}")
    print(f"Sample Block Size: {hex(stmInfo.sampleBlk_size)}")
    print(f"Sample Block Sample Count: {str(stmInfo.sampleBlk_sampleCount)}")
    print(f"Last Sample Block Size: {hex(stmInfo.lSampleBlk_size)}")
    print(f"Last Sample Block Sample Count: {str(stmInfo.lSampleBlk_sampleCount)}")
    print(f"Last Sample Block Padded Size: {hex(stmInfo.lSampleBlk_padSize)}")
    print(f"Seek Data Size: {hex(stmInfo.seek_size)}")
    print(f"Seek Interval Sample Count: {str(stmInfo.SISC)}")

    pos += stmInfo.size

    sampleData_ref = Ref(bom)
    sampleData_ref.data(f, pos)

    if sampleData_ref.offset not in [0, -1]:
        for i in range(1, header.numBlocks + 1):
            if sized_refs[i].offset not in [0, -1]:
                if sized_refs[i].type_  == 0x4002:
                    print(f"Sample Data offset: {hex(sampleData_ref.offset + sized_refs[i].offset + 8)}")
                if sized_refs[i].type_  == 0x4004:
                    print(f"Prefetch Data offset: {hex(sampleData_ref.offset)}")

    pos += 8

    trkInfoTable = {}
    trkInfo = {}

    if trkInfoTable_ref.offset not in [0, -1]:
        pos = trkInfoTable_ref.offset + stmInfo_ref.pos
        count = struct.unpack(f"{bom}I", f[pos:pos + 4])[0]
        pos += 4

        for i in range(1, count + 1):
            pos = trkInfoTable_ref.offset + stmInfo_ref.pos + 4
            trkInfoTable[i] = Ref(bom)
            trkInfoTable[i].data(f, pos + 8 * (i - 1))

            if trkInfoTable[i].offset not in [0, -1]:
                print(f"\nTrack Info Entry {str(i)} offset: {hex(trkInfoTable[i].offset + pos - 4)}")

                pos = trkInfoTable[i].offset + pos - 4
                trkInfo[i] = TRKInfo(bom)
                trkInfo[i].data(f, pos)

                print(f"Volume: {str(trkInfo[i].volume)}")
                print(f"Pan: {str(trkInfo[i].pan)}")
                print(f"Unknown value: {str(trkInfo[i].unk)}")
                pos += trkInfo[i].size
                channelIndexByteTable_ref = Ref(bom)
                channelIndexByteTable_ref.data(f, pos)

                if channelIndexByteTable_ref.offset not in [0, -1]:
                    print(f"Channel Index Byte Table offset: {hex(
                        channelIndexByteTable_ref.offset + pos - trkInfo[i].size)}")

                    pos = channelIndexByteTable_ref.offset + pos - trkInfo[i].size
                    count = struct.unpack(f"{bom}I", f[pos:pos + 4])[0]
                    pos += 4
                    elem = f[pos:pos + count]

                    print(f"Elements: {str(elem)}")

    channelInfoTable = {}
    ADPCMInfo_ref = {}

    pos = channelInfoTable_ref.offset + stmInfo_ref.pos
    count = struct.unpack(f"{bom}I", f[pos:pos + 4])[0]
    pos += 4

    for i in range(1, count + 1):
        pos = channelInfoTable_ref.offset + stmInfo_ref.pos + 4
        channelInfoTable[i] = Ref(bom)
        channelInfoTable[i].data(f, pos + 8 * (i - 1))

        if channelInfoTable[i].offset not in [0, -1]:
            print(f"\nChannel {str(i)} Info Entry ADPCM Info Reference offset: {hex(
                channelInfoTable[i].offset + pos - 4)}")

            pos = channelInfoTable[i].offset + pos - 4
            ADPCMInfo_ref[i] = Ref(bom)
            ADPCMInfo_ref[i].data(f, pos)

            if ADPCMInfo_ref[i].offset not in [0, -1]:
                print(f"\nADPCM Info offset: {hex(ADPCMInfo_ref[i].offset + pos)}")
                print(f"Type: {hex(ADPCMInfo_ref[i].type_)}")

                pos = ADPCMInfo_ref[i].offset + pos
                if ADPCMInfo_ref[i].type_ == 0x0300:
                    param = b''
                    for i in range(1, 17):
                        param += struct.unpack(f"{bom}H", f[pos + 2 * (i - 1):pos + 2 * (i - 1) + 2])[0].to_bytes(2,
                                                                                                                  'big')
                    print(f"Param: {str(param)}")

                    pos += 32
                    context = DSPContext(bom)
                    context.data(f, pos)

                    print(f"Context Predictor and Scale: {hex(context.predictor_scale)}")
                    print(f"Context Previous Sample: {hex(context.preSample)}")
                    print(f"Context Second Previous Sample: {hex(context.preSample2)}")

                    pos += context.size
                    loopContext = DSPContext(bom)
                    loopContext.data(f, pos)

                    print(f"Loop Context Predictor and Scale: {hex(loopContext.predictor_scale)}")
                    print(f"Loop Context Previous Sample: {hex(loopContext.preSample)}")
                    print(f"Loop Context Second Previous Sample: {hex(loopContext.preSample2)}")

                    pos += loopContext.size
                    pos += 2

                elif ADPCMInfo_ref[i].type_ == 0x0301:
                    context = IMAContext(bom)
                    context.data(f, pos)

                    print(f"Context Data: {hex(context.data_)}")
                    print(f"Context Table Index: {hex(context.tableIndex)}")

                    pos += context.size
                    loopContext = IMAContext(bom)
                    loopContext.data(f, pos)

                    print(f"Loop Context Data: {hex(loopContext.data_)}")
                    print(f"Loop Context Table Index: {hex(loopContext.tableIndex)}")

                    pos += loopContext.size

    for i in range(1, header.numBlocks + 1):
        if sized_refs[i].offset not in [0, -1]:
            if sized_refs[i].type_ == 0x4001:
                pos = sized_refs[i].offset
                seek = BLKHeader(bom)
                seek.data(f, pos)

                print('')
                print(f"Seek Block Magic: {bytes_to_string(seek.magic)}")
                print(f"Size: {hex(seek.size_)}")
                pos += seek.size

                seek.data_ = f[pos:pos + seek.size_ - 8]

            elif sized_refs[i].type_ in [0x4002, 0x4004]:
                pos = sized_refs[i].offset
                data = BLKHeader(bom)
                data.data(f, pos)

                print('')
                if sized_refs[i].type_ == 0x4002: print(f"Data Block Magic: {bytes_to_string(data.magic)}")
                else:  print(f"Prefetch Data Block Magic: {bytes_to_string(data.magic)}")
                print(f"Size: {hex(data.size_)}")

                pos += data.size
                data.data_ = f[pos:pos + data.size_ - 8]


def main():
    with open(sys.argv[1], "rb") as inf:
        inb = inf.read()
        inf.close()

    readFile(inb)


if __name__ == '__main__': main()
