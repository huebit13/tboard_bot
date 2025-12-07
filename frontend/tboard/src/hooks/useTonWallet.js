import { useState, useEffect } from 'react';
import { 
  useTonConnectUI, 
  useTonAddress, 
  useTonWallet as useTonConnectWallet 
} from '@tonconnect/ui-react';
import { Address } from 'ton';

// Используем переменные из .env
const TON_API = import.meta.env.VITE_TON_API;
const TON_API_KEY = import.meta.env.VITE_TON_API_KEY;

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
    if (!address) return;
    
    try {
      setLoading(true);
      setError(null);

      const addressObj = Address.parse(address);
      const rawAddress = addressObj.toString({ testOnly: true });

      const response = await fetch(
        `${TON_API}/getAddressBalance?address=${rawAddress}`,
        {
          headers: {
            'X-API-Key': TON_API_KEY
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch balance');
      }

      const data = await response.json();
      
      if (data.ok && data.result) {
        const tonBalance = parseFloat(data.result) / 1e9;
        setBalance(tonBalance);
      }
    } catch (err) {
      console.error('Error fetching balance:', err);
      setError(err.message);
      setBalance(0);
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
    }
  }, [userFriendlyAddress]);

  const connect = async () => {
    try {
      await tonConnectUI.openModal();
    } catch (err) {
      console.error('Error connecting wallet:', err);
      setError(err.message);
    }
  };

  const disconnect = async () => {
    try {
      await tonConnectUI.disconnect();
      setBalance(0);
    } catch (err) {
      console.error('Error disconnecting wallet:', err);
      setError(err.message);
    }
  };

  const sendTransaction = async (to, amount, payload = '') => {
    if (!wallet) {
      throw new Error('Wallet not connected');
    }

    try {
      const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 600,
        messages: [
          {
            address: to,
            amount: (amount * 1e9).toString(),
            payload
          }
        ]
      };

      const result = await tonConnectUI.sendTransaction(transaction);
      return result;
    } catch (err) {
      console.error('Error sending transaction:', err);
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
