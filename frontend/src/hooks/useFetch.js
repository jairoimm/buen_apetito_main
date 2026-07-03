import { useState, useEffect, useCallback } from 'react';
 
const useFetch = (fetchFn, deps = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
 
  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar los datos.');
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
 
  useEffect(() => { fetch(); }, [fetch]);
 
  return { data, loading, error, refetch: fetch };
};
 
export default useFetch;