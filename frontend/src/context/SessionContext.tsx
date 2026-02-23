import { createContext, useContext } from "react";
import type { PredictionMessage } from "../hooks/useWebSocketStream";

type SessionState = {
  history: PredictionMessage[];
};

const Ctx = createContext<SessionState>({ history: [] });

export function useSession() {
  return useContext(Ctx);
}

export default Ctx;

