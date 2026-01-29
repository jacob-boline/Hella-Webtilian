export {};

declare global {
  interface Window {
    Stripe?: (publishableKey: string) => {
      initEmbeddedCheckout: (opts: { fetchClientSecret: () => Promise<string> }) => Promise<{
        mount: (el: Element) => void;
      }>;
    };
  }
}
