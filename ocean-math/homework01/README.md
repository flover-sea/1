# 海洋数学基础 · 实践01

四个题目合并报告，按“电子实验报告”页的“实验题目—实验步骤（程序代码）及结果”编排。

## 报告下载

- [PDF 报告](学号-姓名-实践01.pdf)
- [可编辑 Word 报告](学号-姓名-实践01.docx)
- [下载仓库全部文件（ZIP）](https://github.com/flover-sea/1/archive/refs/heads/main.zip)

打开 PDF 或 Word 页面后，点击右上角下载按钮。填写学号、姓名后，按要求命名为“学号-姓名-实践01.pdf”。ZIP 解压后，作业位于 `ocean-math/homework01/`。

## 运行 Python 程序

```bash
python3 -m pip install -r requirements.txt
python3 run_experiments.py
```

程序将结果写入脚本所在目录。仅依赖 NumPy 和 Matplotlib。

`interpolation.py` 提供四个通用函数，可直接传入任意互异节点、数据和查询点；不限于题目给定数值：

```python
from interpolation import lagrange, piecewise_linear, hermite_global, hermite_piecewise

print(lagrange([0, 1, 2], [0, 1, 4], 0.5))
print(piecewise_linear([0, 1, 2], [0, 1, 4], [0.5, 1.5]))
print(hermite_global([0, 1], [0, 1], [0, 2], 0.5))
print(hermite_piecewise([0, 1], [0, 1], [0, 2], 0.5))
```

默认拒绝外推，显式传入 `extrapolate=True` 可允许外推。支持标量及任意形状查询数组，自动对节点排序并校验输入。

## 文件

- `interpolation.py`：通用插值算法。
- `run_experiments.py`：四题计算、绘图和结果导出。
- `result1.csv` 至 `result4.csv`：全部查询点结果。
- `nodes4.csv`：第四题函数值和导数。
- `figure1.png` 至 `figure4.png`：实验图。
- `summary.json`：关键数值。
- `验证记录.txt`：核对记录。

第一题使用题目给出的六位小数节点值。第二题使用全部8个节点构造七次 Lagrange 插值。第四题使用给定真实导数；“九次”表示次数不超过9，由于本题对称性，实际得到八次偶多项式。
