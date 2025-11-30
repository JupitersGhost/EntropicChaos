# utils.py
import math
import time
from collections import Counter

def calculate_shannon_entropy(data_bytes):
    if not data_bytes:
        return 0.0
    length = len(data_bytes)
    counts = Counter(data_bytes)
    entropy = 0.0
    for count in counts.values():
        p_x = count / length
        entropy -= p_x * math.log2(p_x)
    return entropy

def get_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def fmt_bytes(b_data):
    return b_data.hex().upper()

class HealthMonitor:
    """
    Implements lightweight health checks inspired by NIST SP 800-90B.
    Prevents low-quality entropy (like stuck pixels or muted mics) 
    from contaminating the pool.
    """
    @staticmethod
    def repetition_count_test(data, cutoff=10):
        """
        Fails if any single value repeats continuously more than 'cutoff' times.
        Returns: (Passed Bool, Details String)
        """
        if not data: return True, "Empty"
        
        max_repeats = 0
        current_repeats = 0
        last_val = None
        
        for byte in data:
            if byte == last_val:
                current_repeats += 1
            else:
                max_repeats = max(max_repeats, current_repeats)
                current_repeats = 1
                last_val = byte
                
        max_repeats = max(max_repeats, current_repeats)
        
        if max_repeats >= cutoff:
            return False, f"RCT Fail (Repeats: {max_repeats})"
        return True, "OK"

    @staticmethod
    def adaptive_proportion_test(data, cutoff_ratio=0.40):
        """
        Fails if the most common value dominates the sample.
        """
        if not data: return True, "Empty"
        
        # Find most common byte
        counts = Counter(data)
        most_common = counts.most_common(1)[0] # (byte, count)
        ratio = most_common[1] / len(data)
        
        if ratio > cutoff_ratio:
            return False, f"APT Fail (Dominance: {ratio:.2%})"
        return True, "OK"