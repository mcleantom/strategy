import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import './App.css';
import { StrategyService } from './client';
import { BacktestResult } from './client';
import { OpenAPI } from './client';
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Link
} from "react-router-dom";
import Backtest from './pages/Backtest';
import Test from './pages/Test';

OpenAPI.BASE = "http://localhost:8000";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Backtest/>}/>
        <Route path="/test" element={<Test/>}/>
      </Routes>
    </Router>
  )
}