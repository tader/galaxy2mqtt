import { PassiveRFPanel } from "./passive_rf_panel";

test('should construct object', () => {
    const passiveRFPanel = new PassiveRFPanel(0x10);
    expect(passiveRFPanel).toBeInstanceOf(PassiveRFPanel);
});

// test('should parse buffer', () => {
//     const passiveRFPanel = new PassiveRFPanel(0x10);
//     expect(passiveRFPanel).toBeInstanceOf(PassiveRFPanel);

//     passiveRFPanel.ingest(Buffer.from([
//         0x10, 0x01, 0x02,
//         0x11, 0x03, 0x04,
//     ]));

//     return new Promise<void>((resolve, reject) => {
//         passiveRFPanel.on('parsed', (res) => {
//             expect(res).toEqual(Buffer.from([0x11, 0x03, 0x04]));
//             resolve();
//         } );
//         passiveRFPanel.on('error', (err) => { reject(err); } );
//     });
// });