import * as checksum from "./checksum"

test('should convert number 256 to bytes', () => {
    const bytes = checksum.numberToBytes(256);
    expect(bytes.length).toEqual(2);
    expect(bytes[0]).toEqual(0);
    expect(bytes[1]).toEqual(1);
});

test('should calculate checksum for empty buffer', () => {
    const data: Uint8Array = new Uint8Array([]);
    expect(checksum.calculate(data)).toEqual(0xAA);
});

test('should calculate checksum for packet', () => {
    const data: Uint8Array = new Uint8Array([0x11, 0xfd, 0x01, 0x0a, 0x1b, 0x1c, 0x00, 0x06, 0x00, 0x00, 0x02, 0x0a]);
    expect(checksum.calculate(data)).toEqual(0x0e);
});