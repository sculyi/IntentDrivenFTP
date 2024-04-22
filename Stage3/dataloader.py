# coding=utf-8
import logging
import random
import numpy as np
import torch.utils.data as da

RNG_SEED = 123
logger = logging.getLogger(__name__)

from utils import convert_text_to_ids, seq_padding

from transformers import BertTokenizer
import pandas as pd

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.max_rows', 1000)
pd.set_option('display.width', 10000)
pd.set_option('display.max_colwid', 1000)


class DataGenerator(da.Dataset):
    def __init__(self, configs):
        self.configs = configs
        # self.rng = random.Random(RNG_SEED)
        self.data_num = 0
        self.datas = []

        self.target_size = {'lon': self.configs.delta_lon_size,
                            'lat': self.configs.delta_lat_size,
                            'alt': self.configs.delta_alt_size,
                            'spdx': self.configs.delta_spdx_size,
                            'spdy': self.configs.delta_spdy_size,
                            'spdz': self.configs.delta_spdz_size}

        self.tokenizer = BertTokenizer(vocab_file=self.configs.vocab_path, model_max_length=512)

    def load_data_from_dir(self, data_path):
        self.datas = pd.read_csv(data_path)
        print(data_path, 'data num:', len(self.datas))

        self.data_num = len(self.datas)

    def __len__(self):
        return len(self.datas)

    def __getitem__(self, index):
        row = self.datas.loc[index, :]
        text = row.text
        trk_path = row.trk_path
        trks = pd.read_csv(trk_path)

        if self.configs.is_training:
            idx = random.randint(1, 4)
        else:
            idx = 1

        lon = trks.lon.tolist()[self.configs.data_period - idx::self.configs.data_period]
        lat = trks.lat.tolist()[self.configs.data_period - idx::self.configs.data_period]
        alt = trks.alt.tolist()[self.configs.data_period - idx::self.configs.data_period]
        spdy = trks.spdy.tolist()[self.configs.data_period - idx::self.configs.data_period]
        spdx = trks.spdx.tolist()[self.configs.data_period - idx::self.configs.data_period]
        spdz = trks.spdz.tolist()[self.configs.data_period - idx::self.configs.data_period]

        return [text, lon, lat, alt, spdx, spdy, spdz]

    def convert_lon2binary(self, lon):
        lon = round(lon, 3) * 1000
        bin_lon = '{0:b}'.format(int(lon)).zfill(self.configs.lon_size)
        bin_lon_list = [int(i) for i in bin_lon]
        assert len(bin_lon_list) == self.configs.lon_size, "ERROR"
        return np.array(bin_lon_list)

    def convert_lat2binary(self, lat):
        lat = round(lat, 3) * 1000
        bin_lat = '{0:b}'.format(int(lat)).zfill(self.configs.lat_size)
        bin_lat_list = [int(i) for i in bin_lat]
        assert len(bin_lat_list) == self.configs.lat_size, "ERROR"
        return np.array(bin_lat_list)

    def convert_alt2binary(self, alt):
        alt = int(alt / 10)
        if alt > 15000:
            alt = 0
        bin_alt = '{0:b}'.format(int(alt)).zfill(self.configs.alt_size)
        bin_alt_list = [int(i) for i in bin_alt]

        assert len(bin_alt_list) == self.configs.alt_size, "ERROR {},{}".format(alt, bin_alt)
        return np.array(bin_alt_list)

    def convert_spdx2binary(self, spdx):
        spdx = round(spdx)
        bin_spdx = str(bin(int(spdx)))
        if bin_spdx.startswith('-0b'):
            bin_spdx = '{0:b}'.format(int(-spdx)).zfill(self.configs.spdx_size - 1)
            bin_spdx_list = [1] + [int(i) for i in bin_spdx]
        else:
            bin_spdx = '{0:b}'.format(int(spdx)).zfill(self.configs.spdx_size)
            bin_spdx_list = [int(i) for i in bin_spdx]

        assert len(bin_spdx_list) == self.configs.spdx_size, "ERROR"
        return np.array(bin_spdx_list)

    def convert_spdy2binary(self, spdy):
        spdy = round(spdy)
        bin_spdy = str(bin(int(spdy)))
        if bin_spdy.startswith('-0b'):
            bin_spdy = '{0:b}'.format(int(-spdy)).zfill(self.configs.spdy_size - 1)
            bin_spdy_list = [1] + [int(i) for i in bin_spdy]
        else:
            bin_spdy = '{0:b}'.format(int(spdy)).zfill(self.configs.spdy_size)
            bin_spdy_list = [int(i) for i in bin_spdy]

        assert len(bin_spdy_list) == self.configs.spdy_size, "ERROR"
        return np.array(bin_spdy_list)

    def convert_spdz2binary(self, spdz):
        spdz = round(spdz)

        bin_spdz = bin(int(spdz))
        if bin_spdz.startswith('-0b'):
            bin_spdz = '{0:b}'.format(int(-spdz)).zfill(self.configs.spdz_size - 1)
            bin_spdz_list = [1] + [int(i) for i in bin_spdz]
        else:
            bin_spdz = '{0:b}'.format(int(spdz)).zfill(self.configs.spdz_size)
            bin_spdz_list = [int(i) for i in bin_spdz]

        assert len(bin_spdz_list) == self.configs.spdx_size, "ERROR"
        return np.array(bin_spdz_list)

    def prepare_minibatch(self, seqs):
        batch_text = []
        batch_lon, batch_lat, batch_alt, batch_spdx, batch_spdy, batch_spdz = [], [], [], [], [], []
        raw_batch_lon, raw_batch_lat, raw_batch_alt, raw_batch_spdx, raw_batch_spdy, raw_batch_spdz = [], [], [], [], [], []
        batch_t_lon, batch_t_lat, batch_t_alt, batch_t_spdx, batch_t_spdy, batch_t_spdz = [], [], [], [], [], []
        batch_dec_lon, batch_dec_lat, batch_dec_alt, batch_dec_spdx, batch_dec_spdy, batch_dec_spdz = [], [], [], [], [], [],

        for seq in seqs:
            seq_lon, seq_lat, seq_alt, seq_spdx, seq_spdy, seq_spdz = [], [], [], [], [], []
            raw_seq_lon, raw_seq_lat, raw_seq_alt, raw_seq_spdx, raw_seq_spdy, raw_seq_spdz = [], [], [], [], [], []
            t_lon, t_lat, t_alt, t_spdx, t_spdy, t_spdz = [], [], [], [], [], []
            text = seq[0]
            batch_text.append(text)
            for lon, lat, alt, spdx, spdy, spdz in zip(seq[1], seq[2], seq[3], seq[4], seq[5], seq[6]):
                seq_lon.append(self.convert_lon2binary(lon))
                seq_lat.append(self.convert_lat2binary(lat))
                seq_alt.append(self.convert_alt2binary(alt))
                seq_spdx.append(self.convert_spdx2binary(spdx))
                seq_spdy.append(self.convert_spdy2binary(spdy))
                seq_spdz.append(self.convert_spdz2binary(spdz))

                raw_seq_lon.append(int(lon * 1000))
                raw_seq_lat.append(int(lat * 1000))
                raw_seq_alt.append(alt // 10)
                raw_seq_spdx.append(int(spdx))
                raw_seq_spdy.append(int(spdy))
                raw_seq_spdz.append(int(spdz))

            for step in range(0, self.configs.inp_seq_len + self.configs.horizon):
                t_lon.append(self.convert_tar((raw_seq_lon[step], raw_seq_lon[step - 1]), 'lon'))
                t_lat.append(self.convert_tar((raw_seq_lat[step], raw_seq_lat[step - 1]), 'lat'))
                t_alt.append(self.convert_tar((raw_seq_alt[step], raw_seq_alt[step - 1]), 'alt'))
                t_spdx.append(self.convert_tar((raw_seq_spdx[step], raw_seq_spdx[step - 1]), 'spdx'))
                t_spdy.append(self.convert_tar((raw_seq_spdy[step], raw_seq_spdy[step - 1]), 'spdy'))
                t_spdz.append(self.convert_tar((raw_seq_spdz[step], raw_seq_spdz[step - 1]), 'spdz'))

            batch_lon.append(seq_lon[:self.configs.inp_seq_len])
            batch_lat.append(seq_lat[:self.configs.inp_seq_len])
            batch_alt.append(seq_alt[:self.configs.inp_seq_len])
            batch_spdx.append(seq_spdx[:self.configs.inp_seq_len])
            batch_spdy.append(seq_spdy[:self.configs.inp_seq_len])
            batch_spdz.append(seq_spdz[:self.configs.inp_seq_len])

            batch_t_lon.append(t_lon[self.configs.inp_seq_len:])
            batch_t_lat.append(t_lat[self.configs.inp_seq_len:])
            batch_t_alt.append(t_alt[self.configs.inp_seq_len:])
            batch_t_spdx.append(t_spdx[self.configs.inp_seq_len:])
            batch_t_spdy.append(t_spdy[self.configs.inp_seq_len:])
            batch_t_spdz.append(t_spdz[self.configs.inp_seq_len:])

            batch_dec_lon.append(t_lon[:self.configs.inp_seq_len])
            batch_dec_lat.append(t_lat[:self.configs.inp_seq_len])
            batch_dec_alt.append(t_alt[:self.configs.inp_seq_len])
            batch_dec_spdx.append(t_spdx[:self.configs.inp_seq_len])
            batch_dec_spdy.append(t_spdy[:self.configs.inp_seq_len])
            batch_dec_spdz.append(t_spdz[:self.configs.inp_seq_len])

            raw_batch_lon.append(raw_seq_lon)
            raw_batch_lat.append(raw_seq_lat)
            raw_batch_alt.append(raw_seq_alt)
            raw_batch_spdx.append(raw_seq_spdx)
            raw_batch_spdy.append(raw_seq_spdy)
            raw_batch_spdz.append(raw_seq_spdz)

        lons = batch_lon
        lats = batch_lat
        alts = batch_alt
        spdxs = batch_spdx
        spdys = batch_spdy
        spdzs = batch_spdz

        input_ids, token_type_ids = convert_text_to_ids(self.tokenizer, batch_text)
        input_ids = seq_padding(self.tokenizer, input_ids)
        token_type_ids = seq_padding(self.tokenizer, token_type_ids)

        return {
            'lon': lons,
            'lat': lats,
            'alt': alts,
            'spdx': spdxs,
            'spdy': spdys,
            'spdz': spdzs,
            'raw_lon': raw_batch_lon,
            'raw_lat': raw_batch_lat,
            'raw_alt': raw_batch_alt,
            'raw_spdx': raw_batch_spdx,
            'raw_spdy': raw_batch_spdy,
            'raw_spdz': raw_batch_spdz,
            't_lon': batch_t_lon,
            't_lat': batch_t_lat,
            't_alt': batch_t_alt,
            't_spdx': batch_t_spdx,
            't_spdy': batch_t_spdy,
            't_spdz': batch_t_spdz,
            'dec_lon': batch_dec_lon,
            'dec_lat': batch_dec_lat,
            'dec_alt': batch_dec_alt,
            'dec_spdx': batch_dec_spdx,
            'dec_spdy': batch_dec_spdy,
            'dec_spdz': batch_dec_spdz,
            'text': input_ids,
            'token_type': token_type_ids
        }

    def convert_tar(self, d, type='lon'):
        v = d[0] - d[1]

        if v >= 0:
            sign = '0'
        else:
            sign = '1'
            v = -v

        bin = '{0:b}'.format(int(v)).zfill(self.target_size[type] - 1)

        bin = sign + bin

        bin_list = [int(i) for i in bin]

        if len(bin) > self.target_size[type]:
            bin_list = [0] * (self.target_size[type])

        return np.array(bin_list)