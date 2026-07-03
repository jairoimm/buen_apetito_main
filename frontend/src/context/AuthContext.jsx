import React, { createContext, useContext, useState } from 'react';
import { login as apiLogin, logout as apiLogout } from '../api/services';
 
const AuthContext = createContext();
 
export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('access_token')
  );
 
  const login = async (username, password) => {
    await apiLogin(username, password);
    setIsAuthenticated(true);
  };
 
  const logout = () => {
    apiLogout();
    setIsAuthenticated(false);
  };
 
  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
 
export const useAuth = () => useContext(AuthContext);
