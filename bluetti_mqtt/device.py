class BluettiDevice:
    def __init__(self, address: str, type: str, sn: str):
        self.address = address
        self.type = type
        self.sn = sn

    def __repr__(self):
        return (
            f'BluettiDevice(address={self.address}, type={self.type},'
            f' sn={self.sn})'
        )
