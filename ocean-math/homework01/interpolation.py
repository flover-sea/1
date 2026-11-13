"""通用一维插值。仅依赖 NumPy；运行 run_experiments.py 复现实验。"""
import numpy as np


def _data(x, y, dy=None):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 1 or y.shape != x.shape or len(x) < 2:
        raise ValueError('x、y 必须是等长一维数组，至少包含两个节点')
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError('数据必须有限')
    order = np.argsort(x)
    x, y = x[order], y[order]
    if np.any(np.diff(x) <= 0):
        raise ValueError('节点不能重复')
    if dy is None:
        return x, y
    dy = np.asarray(dy, float)
    if dy.shape != x.shape or not np.all(np.isfinite(dy)):
        raise ValueError('导数必须是与节点等长的有限数组')
    return x, y, dy[order]


def _query(q, x, extrapolate):
    q = np.asarray(q, float)
    if not np.all(np.isfinite(q)):
        raise ValueError('查询点必须有限')
    if not extrapolate and np.any((q < x[0]) | (q > x[-1])):
        raise ValueError('查询点超出节点范围；如需外推请指定 extrapolate=True')
    return q


def lagrange(x, y, q, *, extrapolate=False):
    """全部节点的 Lagrange 插值，重心形式；q 可为标量或任意形状数组。"""
    x, y = _data(x, y)
    q = _query(q, x, extrapolate)
    # 仿射缩放减轻节点量纲对权重的影响。
    z = (x - x[0]) / (x[-1] - x[0])
    w = np.ones(len(x))
    for i in range(len(x)):
        w[i] = 1 / np.prod(z[i] - np.delete(z, i))
    result = np.empty(q.size)
    for k, v in enumerate(q.ravel()):
        hits = np.flatnonzero(v == x)
        if hits.size:
            result[k] = y[hits[0]]
        else:
            a = w / ((v - x) / (x[-1] - x[0]))
            result[k] = np.dot(a, y) / np.sum(a)
    return result.reshape(q.shape).item() if q.ndim == 0 else result.reshape(q.shape)


def piecewise_linear(x, y, q, *, extrapolate=False):
    """分段线性插值；显式允许外推时使用端点所在区间。"""
    x, y = _data(x, y)
    q = _query(q, x, extrapolate)
    i = np.clip(np.searchsorted(x, q, side='right') - 1, 0, len(x)-2)
    t = (q-x[i]) / (x[i+1]-x[i])
    return (1-t)*y[i] + t*y[i+1]


def hermite_global(x, y, dy, q, *, extrapolate=False):
    """带一阶导数的全局 Hermite 插值，重复节点 Newton 差商。"""
    x, y, dy = _data(x, y, dy)
    q = _query(q, x, extrapolate)
    z = np.repeat(x, 2)
    n = len(z)
    table = np.zeros((n, n))
    table[:, 0] = np.repeat(y, 2)
    for i in range(1, n):
        table[i, 1] = dy[i//2] if i % 2 else (table[i, 0]-table[i-1, 0])/(z[i]-z[i-1])
    for j in range(2, n):
        for i in range(j, n):
            table[i, j] = (table[i, j-1]-table[i-1, j-1])/(z[i]-z[i-j])
    c = np.diag(table)
    result = np.full_like(q, c[-1], dtype=float)
    for k in range(n-2, -1, -1):
        result = result*(q-z[k]) + c[k]
    return result.item() if q.ndim == 0 else result


def hermite_piecewise(x, y, dy, q, *, extrapolate=False):
    """使用给定真实导数的分段三次 Hermite 插值（不是 PCHIP）。"""
    x, y, dy = _data(x, y, dy)
    q = _query(q, x, extrapolate)
    i = np.clip(np.searchsorted(x, q, side='right')-1, 0, len(x)-2)
    h = x[i+1]-x[i]
    t = (q-x[i])/h
    return ((2*t**3-3*t**2+1)*y[i] + (t**3-2*t**2+t)*h*dy[i]
            + (-2*t**3+3*t**2)*y[i+1] + (t**3-t**2)*h*dy[i+1])
