import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import './App.css';
import { StrategyService } from './client';
import { BacktestResult } from './client';
import { OpenAPI } from './client';

OpenAPI.BASE = "http://localhost:8000";

function App() {
  const chartContainerRef = useRef(null);
  const [backtestedResult, setBacktestedResult] = useState<BacktestResult|null>(null);

  useEffect(() => {
    StrategyService.runStrategyBacktestPost().then(result => setBacktestedResult(result));
  }, []);

  useEffect(() => {
    if (chartContainerRef.current === null || backtestedResult == null) { 
      return;
    }
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        attributionLogo: false
      }
    });

    const equitySeries = chart.addLineSeries({
      color: 'green',
      lineWidth: 2,
    });
    const equityCurveData = backtestedResult.equity_curve
    .map((item) => ({
      time: new Date(item.date).toISOString().split('T')[0],
      value: item.equity,
    }))
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
    .filter((item, index, array) => index === 0 || item.time !== array[index - 1].time);
    equitySeries.setData(equityCurveData);

    const markers = [
      {
        time: new Date(backtestedResult.equity_curve[0].date),
        position: 'belowBar',
        color: '#f68410',
        shape: 'circle',
        text: 'BUY',
      }
    ];
    equitySeries.setMarkers(markers);

    const baselineSeries = chart.addLineSeries({
      color: 'red',
      lineWidth: 2,
    });
    const baselineCurveData = backtestedResult.baseline
    .map((item) => ({
      time: new Date(item.date).toISOString().split('T')[0],
      value: item.close,
    }))
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
    .filter((item, index, array) => index === 0 || item.time !== array[index - 1].time);
    baselineSeries.setData(baselineCurveData);
    
    chart.timeScale().fitContent();
    return () => {
      chart.remove();
    };
  }, [backtestedResult]);

  return (
    <div className="App" style={{width: "100vw", height: "100vh"}}>
      <div ref={chartContainerRef} style={{ position: 'relative', width: '100%', height: '100%' }} />
    </div>
  );
}

export default App;
