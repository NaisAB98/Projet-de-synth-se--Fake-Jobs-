import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ClipLoader from 'react-spinners/ClipLoader';
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import './App.css';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('tweet');
  const [tweetContent, setTweetContent] = useState<string>('');
  const [retweets, setRetweets] = useState<number>(0);
  const [comments, setComments] = useState<number>(0);
  const [likes, setLikes] = useState<number>(0);
  const [covidResult, setCovidResult] = useState<string>('');
  const [authenticityResult, setAuthenticityResult] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [registrationUsername, setRegistrationUsername] = useState<string>('');
  const [registrationPassword, setRegistrationPassword] = useState<string>('');
  const [registrationMessage, setRegistrationMessage] = useState<string>('');
  const [loginMessage, setLoginMessage] = useState<string>('');
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [searchHistory, setSearchHistory] = useState<
    Array<{ content: string; result: string; timestamp: string }>
  >([]);
  const [articleName, setArticleName] = useState<string>('');
  const [articleContent, setArticleContent] = useState<string>('');
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [resultsPerPage] = useState<number>(10);

  const fetchSearchHistory = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/search-history', {
        params: { page: pageNumber, results_per_page: resultsPerPage },
        withCredentials: true,
      });
      setSearchHistory(response.data.history);
    } catch (error) {
      console.error('Error fetching search history:', error);
    }
  };

  const handleTweetSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setCovidResult('');
    setAuthenticityResult('');
    try {
      const response = await axios.post(
        'http://localhost:5000/api/check-tweet',
        { content: tweetContent, retweets, comments, likes },
        {
          headers: { 'Content-Type': 'application/json; charset=UTF-8' },
          withCredentials: true,
        }
      );
      const data = response.data;
      setCovidResult(data.covid_result);

      setTimeout(() => {
        setAuthenticityResult(data.authenticity_result);
        setLoading(false);
      }, 2000);

      if (isLoggedIn) {
        await fetchSearchHistory();
      }
    } catch (error) {
      console.error('Error checking tweet:', error);
      setCovidResult('An error occurred while checking the tweet.');
      setLoading(false);
    }
  };

  const handleArticleCheckSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setCovidResult('');
    setAuthenticityResult('');
    setLoading(true);
    try {
      const response = await axios.post(
        'http://localhost:5000/api/check-article',
        { article_name: articleName, article_content: articleContent },
        {
          headers: { 'Content-Type': 'application/json; charset=UTF-8' },
          withCredentials: true,
        }
      );
      const data = response.data;
      setCovidResult(data.covid_result);

      setTimeout(() => {
        setAuthenticityResult(data.authenticity_result);
        setLoading(false);
      }, 2000);

    } catch (error) {
      console.error('Error checking article:', error);
      setCovidResult('An error occurred while checking the article.');
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setRegistrationMessage('');
    try {
      const response = await axios.post(
        'http://localhost:5000/api/register',
        { username: registrationUsername, password: registrationPassword },
        {
          headers: { 'Content-Type': 'application/json; charset=UTF-8' },
          withCredentials: true,
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
          withCredentials: true,
        }
      );
      setLoginMessage(response.data.message);
      if (response.status === 200) {
        setIsLoggedIn(true);
        await fetchSearchHistory();
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
          withCredentials: true,
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

  const handlePrevPage = () => {
    if (pageNumber > 1) {
      setPageNumber(pageNumber - 1);
    }
  };

  const handleNextPage = () => {
    const maxPageNumber = Math.ceil(searchHistory.length / resultsPerPage);
    if (pageNumber < maxPageNumber) {
      setPageNumber(pageNumber + 1);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      if (isLoggedIn) {
        await fetchSearchHistory();
      }
    };
    fetchData();
  }, [isLoggedIn, pageNumber, resultsPerPage]);

  const renderResultIcon = (result: string) => {
    const iconSize = 48; // Increase the size of the icon
    if (result.toLowerCase().includes('vrai')) {
      return <FaCheckCircle className="result-icon" color="green" size={iconSize} />;
    } else if (result.toLowerCase().includes('faux')) {
      return <FaTimesCircle className="result-icon" color="red" size={iconSize} />;
    }
    return null;
  };
  
  const handleDeleteAccount = async () => {
  try {
    const response = await axios.post(
      'http://localhost:5000/api/delete-account',
      {},
      {
        headers: { 'Content-Type': 'application/json; charset=UTF-8' },
        withCredentials: true,
      }
    );
    
    alert(response.data.message); // Affiche le message de succès ou d'échec
    
    if (response.status === 200) {
      setIsLoggedIn(false); // Déconnexion de l'utilisateur côté client
      setSearchHistory([]); // Efface l'historique de recherche

      // Redirection vers la page d'utilisateur non connecté
      window.location.replace('/'); // Vous pouvez remplacer '/' par l'URL de votre choix
    }
  } catch (error) {
    console.error('Erreur lors de la suppression du compte :', error);
    alert('Une erreur s\'est produite lors de la suppression du compte.');
  }
};


  return (
    <div className="App">
      <header className="App-header">
        <h1>Coronavirus Fact Checker</h1>
      </header>
      <div className="container">
        <div className="tabs">
          <button className={activeTab === 'tweet' ? 'active' : ''} onClick={() => setActiveTab('tweet')}>
            Check Tweet
          </button>
          <button className={activeTab === 'article' ? 'active' : ''} onClick={() => setActiveTab('article')}>
            Check Article
          </button>
        </div>
        <div className="tab-content">
          {activeTab === 'tweet' && (
            <div>
              <h2>Check Tweet</h2>
              <form className="tweet-form" onSubmit={handleTweetSubmit}>
                <textarea
                  className="tweet-textarea"
                  value={tweetContent}
                  onChange={e => setTweetContent(e.target.value)}
                  placeholder="Enter tweet content"
                  required
                />
                <div className="numeric-inputs">
                  <label>
                    Retweets
                    <input type="number" value={retweets} onChange={e => setRetweets(Number(e.target.value))} required />
                  </label>
                  <label>
                    Comments
                    <input type="number" value={comments} onChange={e => setComments(Number(e.target.value))} required />
                  </label>
                  <label>
                    Likes
                    <input type="number" value={likes} onChange={e => setLikes(Number(e.target.value))} required />
                  </label>
                </div>
                <button type="submit" className="submit-button">
                  Check Tweet
                </button>
              </form>
              {loading ? (
                <ClipLoader color={'#123abc'} loading={loading} size={150} />
              ) : (
                covidResult && (
                  <div className="result">
                    <h3>Covid Result:</h3>
                    <div className="result-text">
                                            {covidResult}
                      {renderResultIcon(covidResult)}
                    </div>
                  </div>
                )
              )}
              {authenticityResult && (
                <div className="result">
                  <h3>Authenticity Result:</h3>
                  <div className="result-text">
                    {authenticityResult}
                    {renderResultIcon(authenticityResult)}
                  </div>
                </div>
              )}
            </div>
          )}
          {activeTab === 'article' && (
            <div>
              <h2>Check Article</h2>
              <form className="article-form" onSubmit={handleArticleCheckSubmit}>
                <input
                  type="text"
                  value={articleName}
                  onChange={e => setArticleName(e.target.value)}
                  placeholder="Enter article name"
                  required
                />
                <textarea
                  className="article-textarea"
                  value={articleContent}
                  onChange={e => setArticleContent(e.target.value)}
                  placeholder="Enter article content"
                  required
                />
                <button type="submit" className="submit-button">
                  Check Article
                </button>
              </form>
              {loading ? (
                <ClipLoader color={'#123abc'} loading={loading} size={150} />
              ) : (
                covidResult && (
                  <div className="result">
                    <h3>Covid Result:</h3>
                    <div className="result-text">
                      {covidResult}
                      {renderResultIcon(covidResult)}
                    </div>
                  </div>
                )
              )}
              {authenticityResult && (
                <div className="result">
                  <h3>Authenticity Result:</h3>
                  <div className="result-text">
                    {authenticityResult}
                    {renderResultIcon(authenticityResult)}
                  </div>
                </div>
              )}
            </div>
          )}
          <div className="user-authentication">
            {!isLoggedIn ? (
              <div>
                <h2>Register</h2>
                <form onSubmit={handleRegisterSubmit}>
                  <label>
                    Username
                    <input
                      type="text"
                      value={registrationUsername}
                      onChange={e => setRegistrationUsername(e.target.value)}
                      required
                    />
                  </label>
                  <label>
                    Password
                    <input
                      type="password"
                      value={registrationPassword}
                      onChange={e => setRegistrationPassword(e.target.value)}
                      required
                    />
                  </label>
                  <button type="submit" className="submit-button">Register</button>
                </form>
                {registrationMessage && <p>{registrationMessage}</p>}
                <h2>Login</h2>
                <form onSubmit={handleLoginSubmit}>
                  <label>
                    Username
                    <input
                      type="text"
                      value={username}
                      onChange={e => setUsername(e.target.value)}
                      required
                    />
                  </label>
                  <label>
                    Password
                    <input
                      type="password"
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      required
                    />
                  </label>
                  <button type="submit" className="submit-button">Login</button>
                </form>
                {loginMessage && <p>{loginMessage}</p>}
              </div>
            ) : (
              <div>
                <h2>Search History</h2>
                {searchHistory.length > 0 ? (
                  <div>
                    <ul className="history-list">
                      {searchHistory.map((entry, index) => (
                        <li key={index} className="history-item">
                          <p>Content: {entry.content}</p>
                          <p>Result: {entry.result}</p>
                          <p>Timestamp: {entry.timestamp}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p>No search history found.</p>
                )}
                <button onClick={handleLogout} className="submit-button">Logout</button>
                <button onClick={handleDeleteAccount} className="submit-button">Delete Account</button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;

