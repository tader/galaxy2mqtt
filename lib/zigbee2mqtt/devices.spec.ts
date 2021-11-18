import { PassiveDevice } from "./devices";

test('should parse buffer', () => {
    const req_packet = Buffer.from([0x10, 0x01, 0x02]);
    const res_packet = Buffer.from([0x11, 0x03, 0x04]);
    
    const device = new PassiveDevice(0x10);
    expect(device).toBeInstanceOf(PassiveDevice);

    device.ingest(Buffer.concat([res_packet, req_packet, res_packet, req_packet]));

    return new Promise<void>((resolve, reject) => {
        device.on('parsed', (req, res) => {
            expect(req).toEqual(req_packet);
            expect(res).toEqual(res_packet);
            expect(device.buffer).toEqual(req_packet);
            resolve();
        } );
        device.on('error', (err) => { reject(err); } );
    });
});