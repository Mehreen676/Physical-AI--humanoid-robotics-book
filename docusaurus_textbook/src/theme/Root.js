import ChatWidget from '../components/ChatWidget';
import RagChatbot from '../components/RagChatbot';

export default function Root({ children }) {
  // Feature flag: Use new RagChatbot or legacy ChatWidget
  const useRagChatbot = process.env.REACT_APP_RAG_CHATBOT_ENABLED === 'true';

  return (
    <>
      {children}
      {useRagChatbot ? <RagChatbot /> : <ChatWidget />}
    </>
  );
}
