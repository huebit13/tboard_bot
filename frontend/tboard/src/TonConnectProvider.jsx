
import { TonConnectUIProvider } from '@tonconnect/ui-react';

const manifestUrl = window.location.origin + '/tonconnect-manifest.json';

export function TonConnectProvider({ children }) {
  return (
    <TonConnectUIProvider 
      manifestUrl={manifestUrl}
      actionsConfiguration={{
        twaReturnUrl: 'https://t.me/teleboard_play_bot'
      }}
    >
      {children}
    </TonConnectUIProvider>
  );
}