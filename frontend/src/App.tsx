import './App.css';
import { OpenAPI } from './client';
import {
  BrowserRouter as Router,
  Route,
  Routes
} from "react-router-dom";
import Test from './pages/Test';
import Demo from './pages/Backtest';
import Strategy from './pages/Strategy';

OpenAPI.BASE = "http://localhost:8000";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Strategy/>}/>
        <Route path="/strategies" element={<Strategy/>}/>
        <Route path="/test" element={<Test/>}/>
        <Route path="/backtest" element={<Demo/>}/>
      </Routes>
    </Router>
  )
}