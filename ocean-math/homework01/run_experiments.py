"""运行：python3 run_experiments.py；结果写入脚本所在目录。"""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/ocean_math_mpl')
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from interpolation import lagrange, piecewise_linear, hermite_global, hermite_piecewise

OUT = Path(__file__).resolve().parent


def save_csv(name, columns, header):
    np.savetxt(OUT/name, np.column_stack(columns), delimiter=',', header=header,
               comments='', fmt='%.12g', encoding='utf-8-sig')


def main():
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10})
    x1 = np.array([0, .4, .8, 1.2]); y1 = np.array([1, .921061, .696707, .362358])
    q1 = np.array([.45, .58, .02]); p1 = lagrange(x1, y1, q1)
    g = np.linspace(0, 1.2, 601)
    fig, ax = plt.subplots(figsize=(7.2, 4))
    ax.plot(g, np.cos(g), label='cos(x)'); ax.plot(g, lagrange(x1,y1,g),'--',label='Lagrange P3')
    ax.scatter(x1,y1,label='Nodes'); ax.scatter(q1,p1,marker='x',s=65,label='Queries')
    for x,y in zip(q1,p1): ax.annotate(f'({x:.2f}, {y:.6f})',(x,y),xytext=(5,-22),textcoords='offset points')
    ax.set(xlabel='x (rad)', ylabel='y',title='Experiment 1: cubic Lagrange interpolation'); ax.legend(); ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(OUT/'figure1.png',dpi=190); plt.close(fig)
    save_csv('result1.csv',[q1,p1,np.cos(q1),p1-np.cos(q1)],'x,P3,cos_x,error')
    x2=np.arange(-70,71,20,dtype=float); y2=np.array([2.422,4.128,2.537,1.959,1.870,2.136,2.974,2.307])
    q2=np.arange(-60,61,20,dtype=float); p2=lagrange(x2,y2,q2); g=np.linspace(-70,70,1401)
    fig,ax=plt.subplots(figsize=(7.2,4)); ax.plot(g,lagrange(x2,y2,g),label='Lagrange P7')
    ax.plot(x2,y2,'o--',label='Given nodes / linear guide'); ax.scatter(q2,p2,marker='D',label='Requested values')
    ax.set(xlabel='Latitude (degree)',ylabel='Hs (m)',title='Experiment 2: zonal mean significant wave height'); ax.legend(); ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(OUT/'figure2.png',dpi=190); plt.close(fig)
    save_csv('result2.csv',[q2,p2],'latitude_degree,Hs_m')
    x3=np.arange(11,dtype=float); y3=np.array([0,.79,1.53,2.19,2.71,3.03,3.27,2.89,3.06,3.19,3.29])
    q3=np.linspace(0,10,101); p3=piecewise_linear(x3,y3,q3)
    fig,ax=plt.subplots(figsize=(7.2,4)); ax.plot(q3,p3,label='Piecewise linear'); ax.scatter(x3,y3,label='Nodes')
    ax.set(xlabel='x',ylabel='y',title='Experiment 3: piecewise linear interpolation'); ax.legend(); ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(OUT/'figure3.png',dpi=190); plt.close(fig)
    save_csv('result3.csv',[q3,p3],'x,piecewise_linear')
    x4=np.linspace(-1,1,5); f=lambda x:1/(1+25*x*x)
    df=lambda x:-50*x/(1+25*x*x)**2
    y4=f(x4); d4=df(x4); q4=np.linspace(-1,1,201)
    h9=hermite_global(x4,y4,d4,q4); hp=hermite_piecewise(x4,y4,d4,q4)
    save_csv('result4.csv',[q4,f(q4),h9,hp,h9-f(q4),hp-f(q4)],'x,true,H9,Hpiece,error_H9,error_Hpiece')
    save_csv('nodes4.csv',[x4,y4,d4],'x,f,df')
    fig,axs=plt.subplots(2,1,figsize=(7.2,6.2),sharex=True)
    axs[0].plot(q4,f(q4),label='f(x)'); axs[0].plot(q4,h9,'--',label='Global Hermite H9'); axs[0].plot(q4,hp,':',label='Piecewise cubic Hermite')
    axs[0].scatter(x4,y4,color='black',s=20,label='Nodes'); axs[0].set(ylabel='y',title='Experiment 4: Hermite interpolation'); axs[0].legend()
    axs[1].plot(q4,abs(h9-f(q4)),label='H9 absolute error'); axs[1].plot(q4,abs(hp-f(q4)),label='Piecewise absolute error')
    axs[1].set(xlabel='x',ylabel='Absolute error'); axs[1].legend()
    for ax in axs: ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(OUT/'figure4.png',dpi=190); plt.close(fig)
    stats={'q1':q1.tolist(),'p1':p1.tolist(),'err1':(p1-np.cos(q1)).tolist(),
           'q2':q2.tolist(),'p2':p2.tolist(),'err4_global':float(max(abs(h9-f(q4)))),
           'err4_piece':float(max(abs(hp-f(q4))))}
    (OUT/'summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(stats,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
