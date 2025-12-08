import { useState, useEffect } from 'react';
import { 
  useTonConnectUI, 
  useTonAddress, 
  useTonWallet as useTonConnectWallet 
} from '@tonconnect/ui-react';
import { Address } from '@ton/core';

const TON_API = import.meta.env.VITE_TON_API || 'https://testnet.toncenter.com/api/v2';
const TON_API_KEY = import.meta.env.VITE_TON_API_KEY || '';
const IS_TESTNET = TON_API.includes('testnet');

export function useTonWallet() {
  const [tonConnectUI] = useTonConnectUI();
  const userFriendlyAddress = useTonAddress();
  const wallet = useTonConnectWallet();
  
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 4)}...${address.slice(-4)}`;
  };

  const fetchBalance = async (address) => {
    if (!address) {
      setBalance(0);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);

      const addressObj = Address.parse(address);
      const rawAddress = addressObj.toString({ 
        bounceable: true,
        testOnly: IS_TESTNET 
      });

      const url = `${TON_API}/getAddressBalance?address=${rawAddress}`;
      
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (TON_API_KEY) {
        headers['X-API-Key'] = TON_API_KEY;
      }

      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.ok && data.result !== undefined) {
        const tonBalance = parseFloat(data.result) / 1e9;
        setBalance(tonBalance);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      console.error('Error fetching balance:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userFriendlyAddress) {
      fetchBalance(userFriendlyAddress);
      
      const interval = setInterval(() => {
        fetchBalance(userFriendlyAddress);
      }, 10000);

      return () => clearInterval(interval);
    } else {
      setBalance(0);
      setError(null);
    }
  }, [userFriendlyAddress]);

  const connect = async () => {
    try {
      setError(null);
      await tonConnectUI.openModal();
    } catch (err) {
      console.error('Error connecting wallet:', err);
      setError(err.message);
      throw err;
    }
  };

  const disconnect = async () => {
    try {
      setError(null);
      await tonConnectUI.disconnect();
      setBalance(0);
    } catch (err) {
      console.error('Error disconnecting wallet:', err);
      setError(err.message);
      throw err;
    }
  };

  const sendTransaction = async (to, amount, payload = '') => {
    if (!wallet) {
      throw new Error('Wallet not connected');
    }

    try {
      setError(null);
      
      const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 600,
        messages: [
          {
            address: to,
            amount: (amount * 1e9).toString(),
            payload: payload || undefined
          }
        ]
      };

      const result = await tonConnectUI.sendTransaction(transaction);
      
      setTimeout(() => {
        fetchBalance(userFriendlyAddress);
      }, 3000);
      
      return result;
    } catch (err) {
      console.error('Error sending transaction:', err);
      setError(err.message);
      throw err;
    }
  };

  return {
    address: userFriendlyAddress,
    formattedAddress: formatAddress(userFriendlyAddress),
    balance,
    loading,
    error,
    isConnected: !!wallet,
    wallet,
    connect,
    disconnect,
    sendTransaction,
    refreshBalance: () => fetchBalance(userFriendlyAddress)
  };
}