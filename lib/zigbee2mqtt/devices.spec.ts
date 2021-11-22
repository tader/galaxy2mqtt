import { PassiveDevice } from "./devices";

test('should parse buffer', () => {
    const req_packet = Buffer.from([0x10, 0x13, 0x0a, 0xbe, 0x96]);
    const res_packet = Buffer.from([0x11, 0xfd, 0x01, 0x0a, 0x1b, 0x1c, 0x00, 0x06, 0x00, 0x00, 0x02, 0x0a, 0x0e]);
    
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