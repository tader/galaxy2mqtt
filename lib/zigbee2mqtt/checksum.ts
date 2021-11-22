export function numberToBytes(number: number): Uint8Array {
    const bytes: number[] = [];

    var value = Math.floor(number);

    while (value > 0) {
        bytes.push(value & 0xFF);
        value = value >> 8;
    }

    return new Uint8Array(bytes);
}

export function calculate(data: Buffer | Uint8Array): Number {
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

export function validate(data: Buffer | Uint8Array): boolean {
    if (data.length < 2) return false;

    const head = data.slice(0, data.length - 1);
    const tail = data[data.length - 1];

    return calculate(head) == tail;
}