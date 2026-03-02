import { useState, useEffect, useCallback } from "react";
import { authStatus, authLogin, authLogout, authConnections } from "@/lib/api";

interface Connection {
  service: string;
  display_name: string;
  connected: boolean;
}

export function useAuth() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [connections, setConnections] = useState<Connection[]>([]);

  const checkStatus = useCallback(async () => {
    try {
      const status = await authStatus();
      setAuthenticated(status.authenticated);
    } catch {
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async () => {
    try {
      await authLogin();
      await checkStatus();
    } catch (e) {
      console.error("Login failed:", e);
    }
  }, [checkStatus]);

  const logout = useCallback(async () => {
    await authLogout();
    setAuthenticated(false);
  }, []);

  const fetchConnections = useCallback(async () => {
    try {
      const conns = await authConnections();
      setConnections(conns);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  return { authenticated, loading, login, logout, connections, fetchConnections };
}
