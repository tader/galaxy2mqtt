import * as MockBinding from '@serialport/binding-mock';
import * as SerialPort from '@serialport/stream';
import { BaseDevice } from './devices';
import { GalaxyRS485Bus } from './galaxy_rs485';

test('should open serial port', () => {
    const bytes = new Uint8Array([
        0x11, 0xfd, 0x00, 0x29,
        0x65, 0x5d, 0x13, 0x46,
        0xf8, 0x3e, 0x0d, 0x0a,
        0x4d,
    ]);

    SerialPort.Binding = MockBinding;
    MockBinding.createPort('/dev/galaxy');
    
    const port = new SerialPort('/dev/galaxy');

    port.on('open', () => {
        port.binding.emitData(Buffer.from(bytes));
    });

    const bus = new GalaxyRS485Bus(port);
    const device = new BaseDevice(0);
    bus.add(device);

    device.on('data', (data: Buffer) => {
        expect(data.compare(bytes)).toEqual(0);
        port.close();
    });

    return new Promise<void>((resolve, reject) => {
        port.on('close', () => { resolve(); } );
        port.on('error', (err) => { reject(err); } );
    });
});