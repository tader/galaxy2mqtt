import { PassiveDevice } from "./devices";
import * as packets from "./fixtures/packets";

test('should parse buffer', () => {
    const reqPacket = packets.keypadScreenUpdateReq;
    const resPacket = packets.keypadScreenUpdateRes;
    
    const device = new PassiveDevice(0x10);
    expect(device).toBeInstanceOf(PassiveDevice);

    device.ingest(Buffer.concat([resPacket, reqPacket, resPacket, reqPacket]));

    return new Promise<void>((resolve, reject) => {
        device.on('parsed', (req, res) => {
            expect(req).toEqual(reqPacket);
            expect(res).toEqual(resPacket);
            expect(device.buffer).toEqual(reqPacket);
            resolve();
        } );
        device.on('error', (err) => { reject(err); } );
    });
});