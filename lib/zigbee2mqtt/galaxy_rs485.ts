import * as SerialPort from 'serialport';
import { BaseDevice } from './devices';

export class GalaxyRS485Bus {
    port: SerialPort;
    devices: BaseDevice[];

    constructor(port: SerialPort) {
        this.port = port;
        this.devices = [];

        this.port.on('data', (data) => { this.ingest(data); });
    }

    add(device:BaseDevice) {
        this.devices.push(device);
    }

    ingest(data) {
        for (const device of this.devices) {
            device.ingest(data);
        }
    }
}