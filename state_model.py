import json
import time

class StateStore:

    def load(self):
        with open('state.json', 'r') as fp:
            self.state = json.load(fp)

    def flush(self):
        with open('state.json', 'w') as fp:
            json.dump(self.state, fp, indent=4)


    def get(self, dev_type, dev_address, template=None):
        return self.state.get(f'0x{dev_type}{dev_address}', template)

    def set(self, dev_type, dev_address, data):
        self.state[f'0x{dev_type}{dev_address}'] = data
        self.flush()
        return data

    def upsert(self, dev_type, dev_address, attributes=None, allow_joining=True):
        state = self.get(dev_type, dev_address, {'joined': False})
        state['type'] = dev_type
        state['address'] = dev_address
        state['last_seen'] = int(time.time())
        state['count'] = state.get('count', 0) + 1
        if attributes:
            state['attributes'] = attributes
        if allow_joining or state['joined']:
            self.set(dev_type, dev_address, state)
        return state

    def seen(self, dev_type, dev_address):
        state = self.get(dev_type, dev_address)

    def not_seen_for(self, period=60*20):
        now = time.time()

        for name, data in self.state.items():
            if now - data.get('last_seen', 0) > period:
                yield (name, data)


if __name__ == '__main__':
    state = StateStore()
    state.load()
    state.flush()
    state.set('0e', '123456', {'foo': 'bar'})
    state.seen('0e', '123456')
    print(state.get('0e', '123456'))

    for name, data in state.not_seen_for():
        print(name)
