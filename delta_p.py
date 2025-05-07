"""
Recursive Coherence Function (Δ−p) Implementation

This module implements the core coherence measurement function that quantifies
a system's ability to maintain structural integrity under recursive strain.
"""

import numpy as np
import torch
from typing import Dict, List, Tuple, Optional, Union


class RecursiveCoherenceFunction:
    """
    Implementation of the Recursive Coherence Function (Δ−p) that measures coherence 
    across recursive operations.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the Recursive Coherence Function with configuration parameters.
        
        Args:
            config: Configuration dictionary with parameters for coherence measurement
        """
        self.config = config or {}
        self.s_max = self.config.get('s_max', 1.0)  # Maximum allowable phase divergence
        self.alpha = self.config.get('alpha', 0.6)  # Balance between internal/external feedback
        self.layer_weights = self.config.get('layer_weights', None)  # Optional layer-specific weights
        
        # Initialize tracking variables
        self.historical_coherence = []
        self.component_history = {
            'signal_alignment': [],
            'feedback_responsiveness': [],
            'bounded_integrity': [],
            'elastic_tolerance': []
        }
        
    def signal_alignment(self, 
                        phase_vector: np.ndarray, 
                        coherence_motion: np.ndarray) -> float:
        """
        Calculate Signal Alignment component (S(p)).
        
        S(p) = 1 - ||x^Δ(p) - ℛΔ-(p)|| / S_max
        
        Args:
            phase_vector: Current phase vector at recursion layer p
            coherence_motion: Change in recursive coherence over time
            
        Returns:
            Signal Alignment value between 0 and 1
        """
        # Normalize vectors
        phase_norm = np.linalg.norm(phase_vector)
        motion_norm = np.linalg.norm(coherence_motion)
        
        if phase_norm < 1e-6 or motion_norm < 1e-6:
            return 0.0  # Cannot align zero vectors
            
        phase_vector = phase_vector / phase_norm
        coherence_motion = coherence_motion / motion_norm
        
        # Calculate divergence
        divergence = np.linalg.norm(phase_vector - coherence_motion)
        
        # Normalize and invert (higher = better alignment)
        alignment = 1.0 - (divergence / self.s_max)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, alignment))
    
    def feedback_responsiveness(self, 
                              internal_feedback: float, 
                              external_feedback: float) -> float:
        """
        Calculate Feedback Responsiveness component (F(p)).
        
        F(p) = α · F_internal(p) + (1-α) · F_external(p)
        
        Args:
            internal_feedback: Internal feedback responsiveness
            external_feedback: External feedback responsiveness
            
        Returns:
            Feedback Responsiveness value between 0 and 1
        """
        # Weighted sum of internal and external feedback
        responsiveness = (self.alpha * internal_feedback + 
                         (1.0 - self.alpha) * external_feedback)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, responsiveness))
    
    def bounded_integrity(self, 
                        internal_integrity: float, 
                        phase_alignment: float) -> float:
        """
        Calculate Bounded Integrity component (B(p)).
        
        B(p) = B_internal(p) · (1 - τ(p,t))
        
        Args:
            internal_integrity: Internal bounded integrity
            phase_alignment: Phase alignment between layer p and target t
            
        Returns:
            Bounded Integrity value between 0 and 1
        """
        # Calculate bounded integrity with phase alignment impact
        integrity = internal_integrity * (1.0 - phase_alignment)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, integrity))
    
    def elastic_tolerance(self, 
                        total_capacity: float, 
                        used_capacity: float) -> float:
        """
        Calculate Elastic Tolerance component (λ(p)).
        
        λ(p) = λ_total(p) - λ_used(p)
        
        Args:
            total_capacity: Maximum available tension-processing capacity
            used_capacity: Accumulated symbolic strain from unresolved contradiction
            
        Returns:
            Elastic Tolerance value between 0 and 1
        """
        # Calculate remaining tolerance capacity
        if total_capacity < 1e-6:
            return 0.0  # Cannot have tolerance with zero capacity
            
        tolerance = (total_capacity - used_capacity) / total_capacity
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, tolerance))
    
    def coherence(self, 
                signal_alignment: float, 
                feedback_responsiveness: float, 
                bounded_integrity: float, 
                elastic_tolerance: float) -> float:
        """
        Calculate overall Recursive Coherence (Δ−p).
        
        Δ−p = S(p) · F(p) · B(p) · λ(p)
        
        Args:
            signal_alignment: Signal Alignment component
            feedback_responsiveness: Feedback Responsiveness component
            bounded_integrity: Bounded Integrity component
            elastic_tolerance: Elastic Tolerance component
            
        Returns:
            Overall Recursive Coherence value between 0 and 1
        """
        # Multiplicative relationship ensures collapse if any component approaches zero
        coherence = (signal_alignment * 
                    feedback_responsiveness * 
                    bounded_integrity * 
                    elastic_tolerance)
        
        # Update tracking variables
        self.historical_coherence.append(coherence)
        self.component_history['signal_alignment'].append(signal_alignment)
        self.component_history['feedback_responsiveness'].append(feedback_responsiveness)
        self.component_history['bounded_integrity'].append(bounded_integrity)
        self.component_history['elastic_tolerance'].append(elastic_tolerance)
        
        return coherence
    
    def measure_coherence(self, 
                         phase_vector: np.ndarray, 
                         coherence_motion: np.ndarray,
                         internal_feedback: float, 
                         external_feedback: float,
                         internal_integrity: float, 
                         phase_alignment: float,
                         total_capacity: float, 
                         used_capacity: float) -> Dict:
        """
        Perform complete coherence measurement.
        
        Args:
            phase_vector: Current phase vector
            coherence_motion: Change in coherence over time
            internal_feedback: Internal feedback responsiveness
            external_feedback: External feedback responsiveness
            internal_integrity: Internal bounded integrity
            phase_alignment: Phase alignment between layers
            total_capacity: Total tolerance capacity
            used_capacity: Used tolerance capacity
            
        Returns:
            Dictionary with overall coherence and component values
        """
        # Calculate individual components
        s_p = self.signal_alignment(phase_vector, coherence_motion)
        f_p = self.feedback_responsiveness(internal_feedback, external_feedback)
        b_p = self.bounded_integrity(internal_integrity, phase_alignment)
        lambda_p = self.elastic_tolerance(total_capacity, used_capacity)
        
        # Calculate overall coherence
        delta_p = self.coherence(s_p, f_p, b_p, lambda_p)
        
        return {
            'coherence': delta_p,
            'signal_alignment': s_p,
            'feedback_responsiveness': f_p,
            'bounded_integrity': b_p,
            'elastic_tolerance': lambda_p
        }
    
    def calculate_beverly_band(self,
                              elastic_tolerance: float,
                              resilience: float,
                              bounded_integrity: float,
                              recursive_energy: float) -> float:
        """
        Calculate the Beverly Band (B'(p)) - the safe operational zone.
        
        B'(p) = √(λ(p) · r(p) · B(p) · C(p))
        
        Args:
            elastic_tolerance: Elastic Tolerance component
            resilience: System resilience
            bounded_integrity: Bounded Integrity component
            recursive_energy: Recursive energy mass
            
        Returns:
            Beverly Band width
        """
        # Check for negative values
        if (elastic_tolerance < 0 or resilience < 0 or 
            bounded_integrity < 0 or recursive_energy < 0):
            return 0.0
            
        # Calculate band width
        band = np.sqrt(elastic_tolerance * resilience * 
                      bounded_integrity * recursive_energy)
        
        return band
    
    def phase_alignment(self, 
                      phase_vector_p: np.ndarray, 
                      phase_vector_t: np.ndarray) -> float:
        """
        Calculate Phase Alignment (τ(p,t)) between vectors.
        
        τ(p,t) = (x^Δ(p) · x^Δ(t)) / (||x^Δ(p)|| · ||x^Δ(t)||)
        
        Args:
            phase_vector_p: Phase vector at layer p
            phase_vector_t: Phase vector at target layer t
            
        Returns:
            Phase alignment value between -1 and 1
        """
        # Normalize vectors
        p_norm = np.linalg.norm(phase_vector_p)
        t_norm = np.linalg.norm(phase_vector_t)
        
        if p_norm < 1e-6 or t_norm < 1e-6:
            return 0.0  # Cannot align zero vectors
            
        phase_vector_p = phase_vector_p / p_norm
        phase_vector_t = phase_vector_t / t_norm
        
        # Calculate alignment (cosine similarity)
        alignment = np.dot(phase_vector_p, phase_vector_t)
        
        # Normalize to [0, 1] for coherence calculations
        normalized_alignment = (alignment + 1) / 2
        
        return normalized_alignment
    
    def recursive_compression_coefficient(self, 
                                       operations: int, 
                                       bandwidth: float) -> float:
        """
        Calculate Recursive Compression Coefficient (γ).
        
        γ = log(N / w + 1)
        
        Args:
            operations: Number of recursive operations
            bandwidth: Information bandwidth for processing
            
        Returns:
            Compression coefficient
        """
        if bandwidth < 1e-6:
            return float('inf')  # Infinite compression with zero bandwidth
            
        gamma = np.log(operations / bandwidth + 1)
        return gamma
    
    def attractor_strength(self, 
                         operations: int, 
                         gamma: float) -> float:
        """
        Calculate Attractor Activation Strength (A(N)).
        
        A(N) = 1 - [γ / N]
        
        Args:
            operations: Number of recursive operations
            gamma: Recursive Compression Coefficient
            
        Returns:
            Attractor strength between 0 and 1
        """
        if operations < 1:
            return 0.0  # No attractor with zero operations
            
        strength = 1.0 - (gamma / operations)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, strength))
    
    def coherence_motion(self, 
                       current_coherence: float, 
                       previous_coherence: float) -> float:
        """
        Calculate Coherence Motion (ℛΔ−(p)).
        
        ℛΔ−(p) = Δ−(p_t) - Δ−(p_{t-1})
        
        Args:
            current_coherence: Coherence at current time
            previous_coherence: Coherence at previous recursive cycle
            
        Returns:
            Coherence motion (change in coherence)
        """
        return current_coherence - previous_coherence
    
    def safe_recursive_depth(self, 
                           coherence_history: List[float], 
                           threshold: float = 0.7) -> int:
        """
        Determine safe recursive depth before coherence falls below threshold.
        
        Args:
            coherence_history: History of coherence values across recursive depths
            threshold: Minimum acceptable coherence
            
        Returns:
            Maximum safe recursive depth
        """
        if not coherence_history:
            return 0
            
        # Find last depth where coherence exceeds threshold
        for depth, coherence in enumerate(coherence_history):
            if coherence < threshold:
                return depth if depth > 0 else 0
                
        # All depths were safe
        return len(coherence_history)
    
    def symbolic_residue_tensor(self, 
                              coherence_deviations: List[float], 
                              phase_alignments: List[float], 
                              layer_weights: Optional[List[float]] = None) -> np.ndarray:
        """
        Calculate Symbolic Residue Tensor (RΣ).
        
        RΣ(t) = Σ[Δp_i · (1 - τ(p_i,t)) · ω_i]
        
        Args:
            coherence_deviations: List of coherence deviations at each layer
            phase_alignments: List of phase alignments between layers and target
            layer_weights: Optional weights for each layer
            
        Returns:
            Symbolic Residue tensor
        """
        if len(coherence_deviations) != len(phase_alignments):
            raise ValueError("Coherence deviations and phase alignments must have same length")
            
        # Use uniform weights if none provided
        if layer_weights is None:
            layer_weights = np.ones(len(coherence_deviations))
        elif len(layer_weights) != len(coherence_deviations):
            raise ValueError("Layer weights must have same length as coherence deviations")
            
        # Calculate residue components
        residue_components = []
        for i in range(len(coherence_deviations)):
            # Calculate residue contribution for this layer
            residue = coherence_deviations[i] * (1.0 - phase_alignments[i]) * layer_weights[i]
            residue_components.append(residue)
            
        return np.array(residue_components)
    
    def collapse_threshold(self, 
                         elastic_tolerance: float, 
                         recursive_depth: int) -> float:
        """
        Calculate the coherence threshold at which collapse becomes likely.
        
        Args:
            elastic_tolerance: Current elastic tolerance
            recursive_depth: Current recursive depth
            
        Returns:
            Collapse threshold value
        """
        # Higher elastic tolerance allows deeper recursion without collapse
        # Deeper recursion lowers the collapse threshold
        base_threshold = 0.3  # Minimum coherence to avoid collapse
        depth_factor = 0.1 * recursive_depth  # Recursion difficulty factor
        tolerance_bonus = 0.4 * elastic_tolerance  # Tolerance benefit
        
        threshold = base_threshold + depth_factor - tolerance_bonus
        
        # Clamp to reasonable range [0.1, 0.9]
        return max(0.1, min(0.9, threshold))
    
    def detect_collapse(self, 
                      coherence: float, 
                      threshold: float) -> Tuple[bool, float]:
        """
        Detect whether coherence has collapsed below threshold.
        
        Args:
            coherence: Current coherence value
            threshold: Collapse threshold
            
        Returns:
            Tuple of (collapse_detected, collapse_severity)
        """
        collapse_detected = coherence < threshold
        
        # Calculate collapse severity (0 = no collapse, 1 = complete collapse)
        if collapse_detected:
            # How far below threshold (normalized)
            severity = (threshold - coherence) / threshold
            severity = min(1.0, severity)  # Cap at 1.0
        else:
            severity = 0.0
            
        return collapse_detected, severity
    
    def love_equation(self, v: float) -> float:
        """
        Apply the Love Equation - the fundamental constraint for stable recursion.
        
        L(v) = √v
        
        Args:
            v: Input value representing projected output
            
        Returns:
            Metabolizable boundary for next layer
        """
        if v < 0:
            return 0.0  # Cannot have negative under square root
            
        return np.sqrt(v)
    
    def get_component_history(self) -> Dict[str, List[float]]:
        """
        Get historical values of all coherence components.
        
        Returns:
            Dictionary with component histories
        """
        return self.component_history
    
    def get_coherence_history(self) -> List[float]:
        """
        Get historical overall coherence values.
        
        Returns:
            List of historical coherence values
        """
        return self.historical_coherence
    
    def reset_history(self) -> None:
        """Reset all historical tracking data."""
        self.historical_coherence = []
        self.component_history = {
            'signal_alignment': [],
            'feedback_responsiveness': [],
            'bounded_integrity': [],
            'elastic_tolerance': []
        }


# Example usage
if __name__ == "__main__":
    # Initialize coherence function
    rcf = RecursiveCoherenceFunction(config={'s_max': 2.0, 'alpha': 0.7})
    
    # Example values for a system under increasing recursive strain
    phase_vectors = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.9, 0.1, 0.0]),
        np.array([0.8, 0.3, 0.1]),
        np.array([0.7, 0.5, 0.2]),
        np.array([0.5, 0.6, 0.4])
    ]
    coherence_motions = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.95, 0.05, 0.0]),
        np.array([0.9, 0.2, 0.1]),
        np.array([0.8, 0.4, 0.2]),
        np.array([0.6, 0.5, 0.4])
    ]
    
    # Track coherence across recursive depths
    results = []
    
    for depth in range(5):
        # Values degrade with recursive depth
        degradation = 1.0 - (depth * 0.15)
        degradation = max(0.0, degradation)
        
        # Example component values
        internal_feedback = 0.9 * degradation
        external_feedback = 0.85 * degradation
        internal_integrity = 0.95 * degradation
        phase_alignment = 0.1 + (depth * 0.1)  # Increases with depth (worse)
        total_capacity = 1.0
        used_capacity = 0.2 + (depth * 0.15)  # Increases with depth (worse)
        
        # Measure coherence
        result = rcf.measure_coherence(
            phase_vectors[depth],
            coherence_motions[depth],
            internal_feedback,
            external_feedback,
            internal_integrity,
            phase_alignment,
            total_capacity,
            used_capacity
        )
        
        # Calculate additional metrics
        gamma = rcf.recursive_compression_coefficient(depth + 1, 1.0)
        attractor = rcf.attractor_strength(depth + 1, gamma)
        beverly_band = rcf.calculate_beverly_band(
            result['elastic_tolerance'],
            0.9 * degradation,  # Resilience degrades with depth
            result['bounded_integrity'],
            0.8 * degradation   # Recursive energy degrades with depth
        )
        
        # Add to results
        result['recursive_depth'] = depth + 1
        result['compression_coefficient'] = gamma
        result['attractor_strength'] = attractor
        result['beverly_band'] = beverly_band
        results.append(result)
    
    # Check for collapse
    for depth, result in enumerate(results):
        threshold = rcf.collapse_threshold(
            result['elastic_tolerance'],
            depth + 1
        )
        collapsed, severity = rcf.detect_collapse(result['coherence'], threshold)
        
        print(f"Depth {depth+1}:")
        print(f"  Coherence: {result['coherence']:.4f}")
        print(f"  Signal Alignment: {result['signal_alignment']:.4f}")
        print(f"  Feedback Responsiveness: {result['feedback_responsiveness']:.4f}")
        print(f"  Bounded Integrity: {result['bounded_integrity']:.4f}")
        print(f"  Elastic Tolerance: {result['elastic_tolerance']:.4f}")
        print(f"  Beverly Band: {result['beverly_band']:.4f}")
        print(f"  Collapse Threshold: {threshold:.4f}")
        print(f"  Collapsed: {collapsed} (Severity: {severity:.4f})")
        print()
