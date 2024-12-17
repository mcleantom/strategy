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
      },
      timeScale: {
        minBarSpacing: 0.0005,
        rightOffset: 10,
        fixLeftEdge: false,
        fixRightEdge: false
      }
    });

    const equitySeries = chart.addLineSeries({
      color: 'green',
      lineWidth: 2,
    });
    const equityCurveData = backtestedResult.equity_curve
    .map((item) => ({
      time: item.unix_seconds,
      value: item.value,
    }))
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
    .filter((item, index, array) => index === 0 || item.time !== array[index - 1].time);
    equitySeries.setData(equityCurveData);

    const markers = [
      {
        time: backtestedResult.equity_curve[0].unix_seconds,
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
      time: item.unix_seconds,
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
    <div className="App">
      <div ref={chartContainerRef} style={{ position: 'relative', width: '500px', height: '300px' }} />
    </div>
  );
}

export default App;
