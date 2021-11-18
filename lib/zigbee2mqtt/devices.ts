import { EventEmitter } from 'events';
import { nextTick } from 'process';

export class BaseDevice {
    device_address: number;
    panel_address: number;

    emitter: EventEmitter;
    buffer: Buffer;

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
        nextTick(() => { this.parseReqFrom() });
    }

    parseReqFrom(offset = 0) {
        var reqByteOffset = this.buffer.indexOf(this.device_address, offset);

        if (reqByteOffset >= 0) {
            const req = this.buffer.slice(
                reqByteOffset,
                reqByteOffset + 3
            )
            const res = this.buffer.slice(
                reqByteOffset + 3,
                reqByteOffset + 6
            )

            // must check checksums
            // allow others to run in between checks
            // assuming req and res are valid:
            this.buffer = this.buffer.slice(reqByteOffset + 6)
            this.emitter.emit('parsed', req, res);
        }

        // else, nextTick(() => { this.parseReqFrom(reqByteOffset + 1) });
    } 
}

export class ActiveDevice extends BaseDevice {

}