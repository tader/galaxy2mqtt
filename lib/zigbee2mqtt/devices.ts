import { EventEmitter } from 'events';
import { nextTick } from 'process';
import * as checksum from './checksum';

export class BaseDevice {
    device_address: number;
    panel_address: number;

    emitter: EventEmitter;
    buffer: Buffer;

    minimumPacketLength = 3;

    constructor(device_address: number, panel_address = 0x11) {
        this.device_address = device_address;
        this.panel_address = panel_address;
        this.emitter = new EventEmitter();
        this.buffer = Buffer.alloc(0);
    }

    on(eventName: string | symbol, listener: (...args: any[]) => void) {
        this.emitter.on(eventName, listener);
    }

    ingest(data: Buffer) {
        this.buffer = Buffer.concat([this.buffer, data]);
        this.emitter.emit('data', data);
        nextTick(() => { this.parse(); });
    }

    parse() {}
}

export class PassiveDevice extends BaseDevice {
    parse() {
        this.findRequestResponse();

        // if buffer way too long remove first byte
        if (this.buffer.length > 40) {
            this.buffer = this.buffer.slice(1);
        }
    }

    seekPossibleStartOfPacket(): boolean {
        const requestOffset = this.buffer.indexOf(this.device_address);

        if (requestOffset <= 0) {
            this.buffer = Buffer.from([]);
            return false;
        }

        this.buffer = this.buffer.slice(requestOffset);
        if (this.buffer.length < this.minimumPacketLength * 2) return false;

        return true;
    }

    findRequestResponse(): {request:Buffer, response:Buffer} | void {        
        if (!this.seekPossibleStartOfPacket()) return;

        // try all possible response starts
        var responseOffset = this.minimumPacketLength - 1;
        while (true) {
            responseOffset = this.buffer.indexOf(this.panel_address, responseOffset + 1);
            if (responseOffset < 0) break;
            if (responseOffset + this.minimumPacketLength > this.buffer.length) break;

            const request = this.buffer.slice(0, responseOffset);

            if (!checksum.validate(request)) continue;

            // try all possible response lengths
            for (
                var responseEnd = responseOffset + this.minimumPacketLength;
                responseEnd <= this.buffer.length;
                responseEnd++
            ) {
                const response = this.buffer.slice(responseOffset, responseEnd);
                if (checksum.validate(response)) {
                    this.buffer = this.buffer.slice(responseEnd)
                    return {request:request, response: response};
                }
            }
        }
    }

    parseReqFrom(offset = 0) {
        var reqByteOffset = this.buffer.indexOf(this.device_address, offset);

        if (reqByteOffset >= 0) {
            var found = false;

            const req = this.buffer.slice(
                reqByteOffset,
                reqByteOffset + 3
            )
            const res = this.buffer.slice(
                reqByteOffset + 3,
                reqByteOffset + 6
            )

            if (checksum.validate(req) && checksum.validate(res)) {
                this.buffer = this.buffer.slice(reqByteOffset + 6)
                this.emitter.emit('parsed', req, res);
                found = true;
            }

            if (!found) {
                nextTick(() => { this.parseReqFrom(reqByteOffset + 1) });
            }
        }
    }
}

export class ActiveDevice extends BaseDevice {

}