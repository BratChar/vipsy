from math import nan
from unittest import TestCase

import numpy as np
from pyro.optim import Adam
import torch
from sklearn.impute import KNNImputer

from vi import RandomIrt1PL, RandomIrt2PL, RandomIrt3PL, RandomIrt4PL, RandomDina, RandomDino, RandomHoDina, \
    VaeIRT, VIRT, VCDM, VaeCDM, VCCDM, VaeCCDM, VCHoDina, VaeCHoDina


class TestMixin(object):

    def prepare_cuda(self):
        self.cuda = torch.cuda.is_available()
        print('cuda: {0}'.format(torch.cuda.is_available()))
        if self.cuda:
            torch.set_default_tensor_type('torch.cuda.FloatTensor')


class IRTRandomMixin(object):

    def gen_sample(self, random_class, sample_size, **kwargs):
        random_instance = random_class(sample_size=sample_size, **kwargs)
        y = random_instance.y
        np.savetxt(f'{random_class.name or "data"}_{sample_size}.txt', y.numpy())
        if self.cuda:
            y = y.cuda()
        return y, random_instance


class Irt1PLTestCase(TestCase, TestMixin, IRTRandomMixin):

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        y, random_instance = self.gen_sample(RandomIrt1PL, 1000)
        model = VIRT(data=y, model='irt_1pl', subsample_size=1000)
        model.fit(random_instance=random_instance)

    def test_ai(self):
        y, random_instance = self.gen_sample(RandomIrt1PL, 100000)
        model = VaeIRT(data=y, model='irt_1pl', subsample_size=100)
        model.fit(random_instance=random_instance)


class Irt2PLTestCase(TestCase, TestMixin, IRTRandomMixin):

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        y, random_instance = self.gen_sample(RandomIrt2PL, 1000)
        model = VIRT(data=y, model='irt_2pl')
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-1}))

    def test_ai(self):
        y, random_instance = self.gen_sample(RandomIrt2PL, 100000)
        model = VaeIRT(data=y, model='irt_2pl', subsample_size=100)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-2}))


class Irt2PLMissingTestCase(TestCase, TestMixin, IRTRandomMixin):
    # 缺失数据下的变分推断

    def setUp(self):
        self.prepare_cuda()

    def gen_missing_y(self, sample_size=1000, missing_rate=0.1, *args, **kwargs):
        row_y, random_instance = self.gen_sample(RandomIrt2PL, sample_size, *args, **kwargs)
        y_size = row_y.size(0) * row_y.size(1)
        row_idx = torch.randint(0, row_y.size(0), (int(y_size * missing_rate),))
        col_idx = torch.randint(0, row_y.size(1), (int(y_size * missing_rate),))
        row_y[row_idx, col_idx] = -1
        # imputer = KNNImputer(n_neighbors=5, weights="uniform")
        # y_ = imputer.fit_transform(row_y.numpy())
        # return torch.from_numpy(y_), random_instance
        return row_y, random_instance

    def test_bbvi(self):
        y, random_instance = self.gen_missing_y(sample_size=100000, missing_rate=0, item_size=10)
        model = VIRT(data=y, model='irt_2pl', subsample_size=1000)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-2}))

    def test_ai(self):
        y, random_instance = self.gen_missing_y(sample_size=100000, missing_rate=0.1, item_size=10)
        model = VaeIRT(data=y, model='irt_2pl', subsample_size=100)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-2}))


class Irt2PLMultiDimTestCase(TestCase, TestMixin, IRTRandomMixin):
    # 多维项目反应理论

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        mask = torch.ones((2, 10))
        y, random_instance = self.gen_sample(RandomIrt2PL, 1000, x_feature=2, item_size=10, a_lower=1.5, a_upper=2.5,
                                             mask=mask)
        model = VIRT(data=y, model='irt_2pl', x_feature=2)
        model.fit(optim=Adam({'lr': 1e-2}), max_iter=50000, random_instance=random_instance)

    def test_ai(self):
        mask = torch.ones((2, 10))
        mask[-1, -5:] = 0
        y, random_instance = self.gen_sample(RandomIrt2PL, 100000, x_feature=2, item_size=10, mask=mask)
        model = VaeIRT(data=y, model='irt_2pl', subsample_size=100, x_feature=2)
        model.fit(optim=Adam({'lr': 5e-3}), max_iter=50000, random_instance=random_instance)


class Irt3PLTestCase(TestCase, TestMixin, IRTRandomMixin):

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        y, random_instance = self.gen_sample(RandomIrt3PL, 1000)
        model = VIRT(data=y, model='irt_3pl', subsample_size=1000)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 5e-2}), max_iter=50000)

    def test_ai(self):
        y, random_instance = self.gen_sample(RandomIrt3PL, 1000000)
        model = VaeIRT(data=y, model='irt_3pl', subsample_size=100)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 5e-3}), max_iter=50000)


class Irt4PLTestCase(TestCase, TestMixin, IRTRandomMixin):

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        y, random_instance = self.gen_sample(RandomIrt4PL, 1000)
        model = VIRT(data=y, model='irt_4pl', subsample_size=1000)
        model.fit(random_instance=random_instance, max_iter=50000, optim=Adam({'lr': 5e-3}))

    def test_ai(self):
        y, random_instance = self.gen_sample(RandomIrt4PL, 100000)
        model = VaeIRT(data=y, model='irt_4pl', subsample_size=100)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 5e-3}), max_iter=50000)


class CDMRandomMixin(object):

    def gen_sample(self, random_class, sample_size):
        random_instance = random_class(sample_size=sample_size)
        y = random_instance.y
        q = random_instance.q
        np.savetxt(f'{random_class.name or "data"}_{sample_size}.txt', y.numpy())
        np.savetxt(f'{random_class.name or "data"}_{sample_size}_q.txt', q.numpy())
        if self.cuda:
            y = y.cuda()
            q = q.cuda()
        return y, q, random_instance


class DinaTestCase(TestCase, TestMixin, CDMRandomMixin):

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        y, q, random_instance = self.gen_sample(RandomDina, 1000)
        model = VCDM(data=y, q=q, model='dina', subsample_size=1000)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-1}))

    def test_ai(self):
        y, q, random_instance = self.gen_sample(RandomDina, 100000)
        model = VaeCDM(data=y, q=q, model='dina', subsample_size=100)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 5e-2}))


class DinoTestCase(TestCase, TestMixin, CDMRandomMixin):

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        y, q, random_instance = self.gen_sample(RandomDino, 1000)
        model = VCDM(data=y, q=q, model='dino', subsample_size=1000)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-1}))

    def test_ai(self):
        y, q, random_instance = self.gen_sample(RandomDino, 100000)
        model = VaeCDM(data=y, q=q, model='dino', subsample_size=100)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-2}), max_iter=10000)


class PaDinaTestCase(TestCase, TestMixin, CDMRandomMixin):

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        y, q, random_instance = self.gen_sample(RandomDina, 1500)
        model = VCCDM(data=y, q=q, model='dina', subsample_size=1500)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-2}))

    def test_ai(self):
        y, q, random_instance = self.gen_sample(RandomDina, 100000)
        model = VaeCCDM(data=y, q=q, model='dina', subsample_size=100)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-2}))


class PaDinoTestCase(TestCase, TestMixin, CDMRandomMixin):

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        y, q, random_instance = self.gen_sample(RandomDino, 1000)
        model = VCCDM(data=y, q=q, model='dino', subsample_size=1000)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-2}))

    def test_ai(self):
        y, q, random_instance = self.gen_sample(RandomDino, 100000)
        model = VaeCCDM(data=y, q=q, model='dino', subsample_size=100)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-2}))


class PaHoDinaTestCase(TestCase, TestMixin, CDMRandomMixin):

    def setUp(self):
        self.prepare_cuda()

    def test_bbvi(self):
        y, q, random_instance = self.gen_sample(RandomHoDina, 1000)
        model = VCHoDina(data=y, q=q, subsample_size=1000)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 1e-1}))

    def test_ai(self):
        y, q, random_instance = self.gen_sample(RandomHoDina, 100000)
        model = VaeCHoDina(data=y, q=q, subsample_size=100)
        model.fit(random_instance=random_instance, optim=Adam({'lr': 5e-3}))