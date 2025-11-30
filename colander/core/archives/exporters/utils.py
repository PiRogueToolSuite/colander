class Buffer:
    # A lightweight buffer to use with zip library
    def __init__(self):
        self.buf = bytearray()

    def write(self, data):
        self.buf.extend(data)
        return len(data)

    def flush(self):
        pass

    def take(self):
        buf = self.buf
        self.buf = bytearray()
        return bytes(buf)

    def end(self):
        buf = self.buf
        self.buf = None
        return bytes(buf)
