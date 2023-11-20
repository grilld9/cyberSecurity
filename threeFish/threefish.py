import numpy as np
import secrets


class ThreeFish:

    def __init__(self, block_size):
        self.table = [[14, 16, 46, 36, 19, 37, 24, 13, 8, 47, 8, 17, 22, 37],
                      [52, 57, 33, 27, 14, 42, 38, 19, 10, 55, 49, 18, 23, 52],
                      [23, 40, 17, 49, 36, 39, 33, 4, 51, 13, 34, 41, 59, 17],
                      [5, 37, 44, 9, 54, 56, 5, 20, 48, 41, 47, 28, 16, 25],
                      [25, 33, 39, 30, 34, 24, 41, 9, 37, 31, 12, 47, 44, 30],
                      [46, 12, 13, 50, 10, 17, 16, 34, 56, 51, 4, 53, 42, 41],
                      [58, 22, 25, 29, 39, 43, 31, 44, 47, 46, 19, 42, 44, 25],
                      [32, 32, 8, 35, 56, 22, 9, 48, 35, 52, 23, 31, 37, 20]]

        self.tableP = [[0, 3, 2, 1],
                       [2, 1, 4, 7, 6, 5, 0, 3],
                       [0, 9, 2, 13, 6, 11, 4, 15, 10, 7, 12, 3, 1, 4, 5, 8, 1]]

        self.TWEAK_SIZE = 16
        self.KEY_SIZE = block_size // 8
        self.NW = self.KEY_SIZE // 8
        if (block_size == 256) | (block_size == 512):
            self.ROUNDS = 72
        else:
            self.ROUNDS = 80
        self.ROUND_KEYS = self.ROUNDS // 4 + 1

    @staticmethod
    def de_mix(y0: np.uint64, y1: np.uint64, r):
        y1 ^= y0
        x1 = ((y1 << np.uint64(64 - r)) | (y1 >> np.uint64(r)))
        x0 = y0 - x1
        return x0, x1

    @staticmethod
    def mix(x0: np.uint64, x1: np.uint64, r):
        y0 = x0 + x1
        y1 = ((x1 << np.uint64(r)) | (x1 >> np.uint64(64 - r)))
        y1 ^= y0
        return y0, y1

    def generate_round_keys(self, key, tweak):
        last_key = np.uint64(0x1bd11bdaa9fc1a22)
        for k in key:
            last_key ^= k
        key = np.append(key, last_key)
        tweak = np.append(tweak, tweak[0] ^ tweak[1])

        round_keys = np.array([], dtype=np.uint64)
        for s in range(0, self.ROUND_KEYS):
            for i in range(0, self.NW):
                if (i >= 0) & (i <= self.NW - 4):
                    round_keys = np.append(round_keys, key[0])
                elif i == self.NW - 3:
                    round_keys = np.append(round_keys, key[0] + tweak[s % 3])
                elif i == self.NW - 2:
                    round_keys = np.append(round_keys, key[0] + tweak[(s + 1) % 3])
                elif i == self.NW - 1:
                    round_keys = np.append(round_keys, key[0] + np.uint(s))
        return round_keys

    def encrypt(self, key: str, tweak: str, text: str):
        key = np.frombuffer(key.encode(), dtype=np.uint64)
        tweak = np.frombuffer(tweak.encode(), dtype=np.uint64)
        text = np.frombuffer(text.encode(), dtype=np.uint64)
        round_keys = self.generate_round_keys(key, tweak)
        state = text.tolist()
        temp = []
        for d in range(0, self.ROUNDS):
            if d % 4 == 0:
                for i in range(0, text.size):
                    state[i] = np.uint64(np.uint64(state[i]) + round_keys[d // 4 + i])

            temp = []
            for j in range(0, self.NW // 2):
                y1, y2 = self.mix(np.uint64(state[2 * j]), np.uint64(state[2 * j + 1]), self.table[d % 8][j])
                temp.append(y1)
                temp.append(y2)

            for i in range(0, self.NW):
                if self.NW == 4:
                    state[i] = temp[self.tableP[0][i]]
                elif self.NW == 8:
                    state[i] = temp[self.tableP[1][i]]
                elif self.NW == 16:
                    state[i] = temp[self.tableP[2][i]]

        text_encrypted = state
        for i in range(0, self.NW):
            text_encrypted[i] = np.uint64(text_encrypted[i] + round_keys[self.ROUNDS // 4 + i])
        return text_encrypted

    def de_crypt(self, key: str, tweak: str, text: list):
        key = np.frombuffer(key.encode(), dtype=np.uint64)
        tweak = np.frombuffer(tweak.encode(), dtype=np.uint64)
        round_keys = self.generate_round_keys(key, tweak)
        state = []
        for i in range(0, self.NW):
            state.append(text[i] - round_keys[self.ROUNDS // 4 + i])
        for d in reversed(range(0, self.ROUNDS)):
            temp = []
            for i in range(0, self.NW):
                if self.NW == 4:
                    temp.append(state[self.tableP[0][i]])
                elif self.NW == 8:
                    temp.append(state[self.tableP[1][i]])
                elif self.NW == 16:
                    temp.append(state[self.tableP[2][i]])
            state = temp.copy()
            for j in range(0, self.NW // 2):
                x1, x2 = self.de_mix(state[2 * j], state[2 * j + 1], self.table[d % 8][j])
                state[2 * j] = x1
                state[2 * j + 1] = x2
            if d % 4 == 0:
                for i in range(0, self.NW):
                    state[i] = np.uint64(np.uint64(state[i]) - round_keys[d // 4 + i])
        return state