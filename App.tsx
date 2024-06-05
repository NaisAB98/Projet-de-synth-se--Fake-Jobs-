import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const App: React.FC = () => {
  const [tweetContent, setTweetContent] = useState<string>('');
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [registrationMessage, setRegistrationMessage] = useState<string>('');
  const [loginMessage, setLoginMessage] = useState<string>('');
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [searchHistory, setSearchHistory] = useState<Array<{content: string, result: string, timestamp: string}>>([]);

  const handleTweetSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setResult('');
    try {
      console.log("Sending request to server...");
      const response = await axios.post(
        'http://localhost:5000/api/check-tweet',
        { content: tweetContent },
        {
          headers: { 'Content-Type': 'application/json; charset=UTF-8' },
          withCredentials: true // Add this line
        }
      );
      console.log("Received response from server:", response.data);
      setResult(response.data.result);

      // Update search history after checking a tweet
      if (isLoggedIn) {
        fetchSearchHistory();
      }
    } catch (error) {
      console.error('Error checking tweet:', error);
      setResult('An error occurred while checking the tweet.');
    }
    setLoading(false);
  };

  const handleRegisterSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setRegistrationMessage('');
    try {
      const response = await axios.post(
        'http://localhost:5000/api/register',
        { username, password },
        {
          headers: { 'Content-Type': 'application/json; charset=UTF-8' },
          withCredentials: true // Add this line
        }
      );
      setRegistrationMessage(response.data.message);
    } catch (error) {
      console.error('Error registering user:', error);
      setRegistrationMessage('An error occurred while registering the user.');
    }
  };

  const handleLoginSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoginMessage('');
    try {
      const response = await axios.post(
        'http://localhost:5000/api/login',
        { username, password },
        {
          headers: { 'Content-Type': 'application/json; charset=UTF-8' },
          withCredentials: true // Add this line
        }
      );
      setLoginMessage(response.data.message);
      if (response.status === 200) {
        setIsLoggedIn(true);
        fetchSearchHistory(); // Fetch search history on login
      }
    } catch (error) {
      console.error('Error logging in:', error);
      setLoginMessage('An error occurred while logging in.');
    }
  };

  const handleLogout = async () => {
    try {
      const response = await axios.post(
        'http://localhost:5000/api/logout',
        {},
        {
          headers: { 'Content-Type': 'application/json; charset=UTF-8' },
          withCredentials: true // Add this line
        }
      );
      setLoginMessage(response.data.message);
      if (response.status === 200) {
        setIsLoggedIn(false);
        setSearchHistory([]);
      }
    } catch (error) {
      console.error('Error logging out:', error);
      setLoginMessage('An error occurred while logging out.');
    }
  };

  const fetchSearchHistory = async () => {
    try {
      const response = await axios.get(
        'http://localhost:5000/api/search-history',
        {
          headers: { 'Content-Type': 'application/json; charset=UTF-8' },
          withCredentials: true // Add this line
        }
      );
      setSearchHistory(response.data.history);
    } catch (error) {
      console.error('Error fetching search history:', error);
    }
  };

  useEffect(() => {
    if (isLoggedIn) {
      fetchSearchHistory();
    }
  }, [isLoggedIn]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Fake News Checker</h1>
        <form onSubmit={handleTweetSubmit}>
          <textarea
            value={tweetContent}
            onChange={(e) => setTweetContent(e.target.value)}
            placeholder="Enter Tweet Content"
            required
          />
          <button type="submit" disabled={loading}>Check</button>
        </form>
        {loading ? <p>Loading...</p> : <p>{result}</p>}
        {isLoggedIn ? (
          <>
            <button onClick={handleLogout}>Logout</button>
            <p>{loginMessage}</p>
            <h2>Search History</h2>
            <ul>
              {searchHistory.map((item, index) => (
                <li key={index}>
                  <p>{item.timestamp}: {item.content} - {item.result}</p>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <>
            <h2>Login</h2>
            <form onSubmit={handleLoginSubmit}>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter Username"
                required
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter Password"
                required
              />
              <button type="submit">Login</button>
            </form>
            <p>{loginMessage}</p>
            <h2>Register</h2>
            <form onSubmit={handleRegisterSubmit}>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter Username"
                required
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter Password"
                required
              />
              <button type="submit">Register</button>
            </form>
            <p>{registrationMessage}</p>
          </>
        )}
      </header>
    </div>
  );
};

export default App;
