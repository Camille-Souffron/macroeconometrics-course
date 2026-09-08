"""Small, fully trained sequence models using automatic differentiation.

No pretrained weights. Architecture parameters and readout are jointly optimised.
"""
import numpy as np
from core import series, result, require


def estimate(frame,s):
    import autograd.numpy as anp
    from autograd import grad
    y,names=series(frame,s,['gdp_growth','inflation','policy_rate','baa_treasury_spread'])
    lag=int(s.get('lags',4));h=int(s.get('horizon',1));width=int(s.get('hidden',4));epochs=int(s.get('epochs',40))
    require(2<=lag<=12 and 2<=width<=12 and 10<=epochs<=150 and 1<=h<=12,'Use 2–12 input dates/hidden units, 10–150 epochs and 1–12 forecast quarters.')
    architecture=s.get('architecture','rnn');rng=np.random.default_rng(int(s.get('seed',2026)))
    ids=np.arange(lag-1,len(y)-h);x=np.stack([y[t-lag+1:t+1] for t in ids]);target=y[ids+h,0]
    split=int(len(x)*float(s.get('train_fraction',.75)));stop=split-h+1
    require(stop>=60 and len(x)-split>=15,'Insufficient training or test observations.')
    mean=x[:stop].mean(axis=(0,1));scale=x[:stop].std(axis=(0,1));require(np.all(scale>0),'Constant input feature.')
    x=(x-mean)/scale;ym=target[:stop].mean();ys=target[:stop].std();z=(target-ym)/ys;k=x.shape[2]
    shapes={}
    def register(key,shape):shapes[key]=shape
    register('input',(k,width));register('bias',(width,))
    if architecture=='rnn':register('recurrent',(width,width))
    elif architecture=='lstm':register('gates',(k+width,4*width));register('gate_bias',(4*width,))
    elif architecture=='tcn':
        for depth in range(2):register(f'conv{depth}',(2,width,width));register(f'conv_bias{depth}',(width,))
    elif architecture=='transformer':
        for name in ['query','key','value','projection','ff1','ff2']:register(name,(width,width))
    else:raise ValueError('Unknown sequence architecture.')
    register('readout',(width,));register('intercept',(1,))
    slices={};offset=0
    for key,shape in shapes.items():size=int(np.prod(shape));slices[key]=slice(offset,offset+size);offset+=size
    params=rng.normal(scale=.15,size=offset)
    def forward(theta,xx):
        w={key:anp.reshape(theta[slices[key]],shape) for key,shape in shapes.items()};batch=xx.shape[0]
        if architecture=='rnn':
            state=anp.zeros((batch,width))
            for t in range(lag):state=anp.tanh(xx[:,t]@w['input']+state@w['recurrent']+w['bias'])
        elif architecture=='lstm':
            state=anp.zeros((batch,width));cell=anp.zeros((batch,width))
            for t in range(lag):
                gates=anp.concatenate([xx[:,t],state],axis=1)@w['gates']+w['gate_bias'];sig=lambda a:1/(1+anp.exp(-a))
                forget=sig(gates[:,:width]);inp=sig(gates[:,width:2*width]);out=sig(gates[:,2*width:3*width]);candidate=anp.tanh(gates[:,3*width:])
                cell=forget*cell+inp*candidate;state=out*anp.tanh(cell)
        else:
            hidden=anp.tanh(anp.dot(xx,w['input'])+w['bias'])
            if architecture=='tcn':
                for depth in range(2):
                    dilation=2**depth
                    shifted=anp.concatenate([anp.zeros((batch,dilation,width)),hidden[:,:-dilation]],axis=1) if dilation<lag else anp.zeros_like(hidden)
                    hidden=anp.tanh(anp.dot(hidden,w[f'conv{depth}'][0])+anp.dot(shifted,w[f'conv{depth}'][1])+w[f'conv_bias{depth}'])
            else:
                # One causal attention head with deterministic positional coordinates.
                positions=anp.sin(anp.arange(lag)[:,None]/(10000**(anp.arange(width)[None,:]/width)))
                hidden=hidden+positions[None,:,:]
                query=anp.dot(hidden,w['query']);key=anp.dot(hidden,w['key']);value=anp.dot(hidden,w['value'])
                scores=anp.einsum('btd,bsd->bts',query,key)/anp.sqrt(width)
                scores=scores+anp.triu(anp.ones((lag,lag)),1)[None,:,:]*(-1e6)
                scores=scores-anp.max(scores,axis=2,keepdims=True);weights=anp.exp(scores);weights=weights/anp.sum(weights,axis=2,keepdims=True)
                hidden=hidden+anp.dot(anp.einsum('bts,bsd->btd',weights,value),w['projection'])
                hidden=(hidden-anp.mean(hidden,axis=2,keepdims=True))/anp.sqrt(anp.var(hidden,axis=2,keepdims=True)+1e-5)
                hidden=hidden+anp.dot(anp.tanh(anp.dot(hidden,w['ff1'])),w['ff2'])
            state=hidden[:,-1]
        return state@w['readout']+w['intercept'][0]
    penalty=float(s.get('penalty',.001));rate=float(s.get('learning_rate',.01));loss_type=s.get('loss','squared');tau=float(s.get('quantile',.1))
    def loss(theta):
        e=z[:stop]-forward(theta,x[:stop]);base=anp.mean(anp.maximum(tau*e,(tau-1)*e)) if loss_type=='quantile' else anp.mean(e**2)
        return base+penalty*anp.mean(theta**2)
    gradient=grad(loss);m=np.zeros_like(params);v=np.zeros_like(params);losses=[]
    for epoch in range(1,epochs+1):
        g=gradient(params);g=g*min(1,5/(np.linalg.norm(g)+1e-12));m=.9*m+.1*g;v=.999*v+.001*g*g
        params-=rate*(m/(1-.9**epoch))/(np.sqrt(v/(1-.999**epoch))+1e-8);losses.append(float(loss(params)))
    predicted=np.asarray(forward(params,x[split:]))*ys+ym;truth=target[split:];e=truth-predicted
    return result(f'{architecture.upper()} held-out forecasts',{'Observed':truth,'Forecast':predicted},
        {'RMSE':np.sqrt(np.mean(e**2)),'MAE':np.mean(np.abs(e)),'Trained parameters':len(params),'Training observations':stop,'Test observations':len(e),'Check loss':np.mean(np.maximum(tau*e,(tau-1)*e))},
        {'Training objective by epoch':losses,'Learned parameter vector':params},
        'All recurrent, gate, convolution or attention weights and the readout are trained jointly by Adam using automatic differentiation. One fixed chronological training sample, with horizon embargo, supplies all held-out predictions. Standardisation uses training data only. These small networks illustrate the architectures; they are not pretrained foundation models.',x=ids[split:],xlabel='Forecast origin (sample index)',ylabel=names[0])
