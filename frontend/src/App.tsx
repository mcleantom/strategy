import './App.css';
import { OpenAPI } from './client';
import {
  BrowserRouter as Router,
  Route,
  Routes
} from "react-router-dom";
import Test from './pages/Test';
import BacktestResultComponent from './pages/BacktestResult';
import Strategy from './pages/Strategy';
import BacktestsComponent from './pages/Backtest';

OpenAPI.BASE = "http://localhost:8000";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Strategy/>}/>
        <Route path="/strategies" element={<Strategy/>}/>
        <Route path="/test" element={<Test/>}/>
        <Route path="/backtests" element={<BacktestsComponent/>}/>
        <Route path="/backtests/:backtestId" element={<BacktestResultComponent/>}/>
      </Routes>
    </Router>
  )
}