export function numberToBytes(number: number): Uint8Array {
    const bytes: number[] = [];

    var value = Math.floor(number);

    while (value > 0) {
        bytes.push(value & 0xFF);
        value = value >> 8;
    }

    return new Uint8Array(bytes);
}

export function calculate(data: Uint8Array): Number {
    const sum1 = data.reduce(
        (previousValue, currentValue) => previousValue + currentValue,
        0xaa
    );

    const sum2 = numberToBytes(sum1).reduce(
        (previousValue, currentValue) => previousValue + currentValue,
        0
    );

    return sum2 & 0xFF;
}