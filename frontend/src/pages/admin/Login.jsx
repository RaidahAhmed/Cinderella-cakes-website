import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../../lib/api';
import '../../styles/admin.css';

// Renders the login screen for administrators and handles the sign-in process.
export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Sends the user's email and password to the server to check if they are correct.
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevents the page from reloading.
    
    // Attempt to log in and handle any connection or validation issues safely.
    try {
      const res = await login(email, password);
      if (res.access_token) {
        // Save the secure token so the user stays logged in across pages.
        localStorage.setItem('token', res.access_token);
        navigate('/admin');
      } else {
        // Show the specific error message from the server if login is rejected.
        setError(res.message || 'Login failed');
      }
    } catch (err) {
      // Show a general error if the server cannot be reached.
      setError('Connection error');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Admin Login</h1>
        {error && <div className="field-error" style={{marginBottom: '16px'}}>{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label>Email</label>
            <input 
              type="email" 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              required 
            />
          </div>
          <div className="form-field">
            <label>Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              required 
            />
          </div>
          <button type="submit" className="btn btn-gradient btn-block">Login</button>
        </form>
      </div>
    </div>
  );
}
