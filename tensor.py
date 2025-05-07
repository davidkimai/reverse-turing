"""
Symbolic Residue Tensor Implementation

This module implements the Symbolic Residue Tensor (RΣ) that captures and analyzes
patterns of coherence breakdown across different dimensions.
"""

import numpy as np
import torch
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import matplotlib.pyplot as plt
from scipy.spatial import distance


@dataclass
class ResidueComponent:
    """Container for a specific component of symbolic residue."""
    name: str
    data: np.ndarray
    metadata: Dict[str, Any]
    
    def magnitude(self) -> float:
        """Calculate the magnitude of this residue component."""
        return float(np.linalg.norm(self.data))


class SymbolicResidueTensor:
    """
    Implementation of the Symbolic Residue Tensor (RΣ) that captures patterns of
    coherence breakdown across different dimensions.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the Symbolic Residue Tensor.
        
        Args:
            config: Configuration dictionary with parameters for residue analysis
        """
        self.config = config or {}
        
        # Initialize tensor dimensions
        self.layers = self.config.get('layers', 12)  # Number of model layers
        self.tokens = self.config.get('tokens', 100)  # Maximum token sequence length
        self.depths = self.config.get('depths', 5)  # Maximum recursive depths
        
        # Initialize residue class trackers
        self.attribution_voids = []  # R_A: Attribution Voids
        self.token_hesitations = []  # R_T: Token Hesitations
        self.recursive_collapses = []  # R_R: Recursive Collapses
        
        # Full tensor representation
        self.tensor = None
        self.initialize_tensor()
        
        # Historical tracking
        self.history = []
        
    def initialize_tensor(self) -> None:
        """Initialize the full residue tensor with zeros."""
        # Structure: [residue_class, layer, token, depth]
        # residue_class: 0=R_A, 1=R_T, 2=R_R
        self.tensor = np.zeros((3, self.layers, self.tokens, self.depths))
        
    def record_attribution_void(self, 
                               layer: int, 
                               token_position: int, 
                               depth: int,
                               magnitude: float,
                               metadata: Dict[str, Any] = None) -> None:
        """
        Record an Attribution Void (R_A) in the residue tensor.
        
        Args:
            layer: Model layer where the void occurred
            token_position: Token position in the sequence
            depth: Recursive depth
            magnitude: Magnitude of the attribution void
            metadata: Additional information about this void
        """
        if metadata is None:
            metadata = {}
            
        # Bounds checking
        layer = min(max(0, layer), self.layers - 1)
        token_position = min(max(0, token_position), self.tokens - 1)
        depth = min(max(0, depth), self.depths - 1)
        
        # Record in tensor
        self.tensor[0, layer, token_position, depth] = magnitude
        
        # Record detailed information
        void = ResidueComponent(
            name="attribution_void",
            data=np.array([magnitude]),
            metadata={
                "layer": layer,
                "token_position": token_position,
                "depth": depth,
                "timestamp": self.config.get("current_step", 0),
                **metadata
            }
        )
        self.attribution_voids.append(void)
        
    def record_token_hesitation(self,
                               token_position: int,
                               entropy: float,
                               oscillation: float,
                               splitting: float,
                               depth: int,
                               metadata: Dict[str, Any] = None) -> None:
        """
        Record a Token Hesitation (R_T) in the residue tensor.
        
        Args:
            token_position: Token position in the sequence
            entropy: Entropy of the token probability distribution
            oscillation: Oscillation between top candidates
            splitting: Splitting into distinct probability clusters
            depth: Recursive depth
            metadata: Additional information about this hesitation
        """
        if metadata is None:
            metadata = {}
            
        # Bounds checking
        token_position = min(max(0, token_position), self.tokens - 1)
        depth = min(max(0, depth), self.depths - 1)
        
        # Calculate overall hesitation magnitude (using all three components)
        magnitude = np.sqrt(entropy**2 + oscillation**2 + splitting**2)
        
        # Record in tensor (average across all layers)
        self.tensor[1, :, token_position, depth] = magnitude / self.layers
        
        # Record detailed information
        hesitation = ResidueComponent(
            name="token_hesitation",
            data=np.array([entropy, oscillation, splitting]),
            metadata={
                "token_position": token_position,
                "depth": depth,
                "timestamp": self.config.get("current_step", 0),
                **metadata
            }
        )
        self.token_hesitations.append(hesitation)
        
    def record_recursive_collapse(self,
                                depth: int,
                                coherence: float,
                                collapse_threshold: float,
                                severity: float,
                                affected_circuits: List[int],
                                metadata: Dict[str, Any] = None) -> None:
        """
        Record a Recursive Collapse (R_R) in the residue tensor.
        
        Args:
            depth: Recursive depth where collapse occurred
            coherence: Coherence value at collapse
            collapse_threshold: Threshold that was crossed
            severity: Severity of the collapse
            affected_circuits: List of circuits affected by collapse
            metadata: Additional information about this collapse
        """
        if metadata is None:
            metadata = {}
            
        # Bounds checking
        depth = min(max(0, depth), self.depths - 1)
        
        # Record in tensor (across all tokens and relevant layers)
        for circuit in affected_circuits:
            if 0 <= circuit < self.layers:
                self.tensor[2, circuit, :, depth] = severity
        
        # Record detailed information
        collapse = ResidueComponent(
            name="recursive_collapse",
            data=np.array([coherence, collapse_threshold, severity]),
            metadata={
                "depth": depth,
                "affected_circuits": affected_circuits,
                "timestamp": self.config.get("current_step", 0),
                **metadata
            }
        )
        self.recursive_collapses.append(collapse)
        
    def measure_attribution_entropy(self, attribution_matrix: np.ndarray) -> Tuple[float, List[int]]:
        """
        Measure attribution entropy to detect potential voids.
        
        Args:
            attribution_matrix: Matrix of attribution values [layers, tokens]
            
        Returns:
            Tuple of (entropy, void_positions) where void_positions is a list of token positions
        """
        # Normalize attribution matrix
        attr_normalized = attribution_matrix / (np.sum(attribution_matrix, axis=1, keepdims=True) + 1e-10)
        
        # Calculate entropy for each layer
        entropies = -np.sum(attr_normalized * np.log2(attr_normalized + 1e-10), axis=1)
        
        # Detect positions with abnormally high entropy
        threshold = np.mean(entropies) + 2 * np.std(entropies)
        void_positions = list(np.where(entropies > threshold)[0])
        
        return float(np.mean(entropies)), void_positions
        
    def measure_token_hesitation(self, token_probabilities: np.ndarray) -> Dict[str, float]:
        """
        Analyze token probability distribution to measure hesitation.
        
        Args:
            token_probabilities: Probability distribution over vocabulary
            
        Returns:
            Dictionary with hesitation metrics
        """
        # Normalize probabilities
        probs = token_probabilities / (np.sum(token_probabilities) + 1e-10)
        
        # Calculate entropy (flatness of distribution)
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        
        # Find top-k candidates
        k = min(10, len(probs))
        top_indices = np.argsort(probs)[-k:]
        top_probs = probs[top_indices]
        
        # Calculate oscillation (difference between top candidates)
        if len(top_probs) >= 2:
            oscillation = top_probs[0] - top_probs[1]
        else:
            oscillation = 0.0
            
        # Detect splitting (multi-modal distribution)
        if len(top_probs) >= 3:
            # Calculate gaps between consecutive probabilities
            gaps = np.diff(top_probs)
            # Large gap indicates splitting
            splitting = np.max(gaps) / (np.mean(gaps) + 1e-10)
        else:
            splitting = 1.0
            
        return {
            "entropy": float(entropy),
            "oscillation": float(oscillation),
            "splitting": float(splitting)
        }
        
    def detect_recursive_collapse(self, 
                                coherence_values: List[float], 
                                threshold: float = 0.7) -> Tuple[bool, int, float]:
        """
        Detect when recursion collapses based on coherence values.
        
        Args:
            coherence_values: List of coherence values across recursive depths
            threshold: Coherence threshold below which collapse occurs
            
        Returns:
            Tuple of (collapse_detected, collapse_depth, severity)
        """
        if not coherence_values:
            return False, 0, 0.0
            
        # Find first depth where coherence falls below threshold
        for depth, coherence in enumerate(coherence_values):
            if coherence < threshold:
                # Calculate severity as how far below threshold
                severity = (threshold - coherence) / threshold
                return True, depth, float(severity)
                
        # No collapse detected
        return False, len(coherence_values), 0.0
        
    def analyze_residue_pattern(self) -> Dict[str, Any]:
        """
        Analyze the residue tensor to identify patterns.
        
        Returns:
            Dictionary with analysis results
        """
        results = {}
        
        # Check if tensor has been populated
        if np.max(self.tensor) == 0:
            return {"error": "No residue data recorded"}
        
        # 1. Spatial distribution analysis
        spatial_distribution = np.sum(self.tensor, axis=(1, 3))  # Sum over layers and depths
        results["spatial_concentration"] = float(np.max(spatial_distribution) / (np.mean(spatial_distribution) + 1e-10))
        results["spatial_entropy"] = float(-np.sum((spatial_distribution / (np.sum(spatial_distribution) + 1e-10)) * 
                                           np.log2(spatial_distribution / (np.sum(spatial_distribution) + 1e-10) + 1e-10)))
        
        # 2. Temporal evolution (approximated by depth)
        temporal_evolution = np.sum(self.tensor, axis=(1, 2))  # Sum over layers and tokens
        results["temporal_gradient"] = float(np.gradient(temporal_evolution).mean())
        
        # 3. Magnitude spectrum
        magnitude_spectrum = np.sort(self.tensor.flatten())
        results["magnitude_median"] = float(np.median(magnitude_spectrum))
        results["magnitude_variance"] = float(np.var(magnitude_spectrum))
        
        # 4. Phase relationships between residue types
        attribution_pattern = self.tensor[0].flatten()
        hesitation_pattern = self.tensor[1].flatten()
        collapse_pattern = self.tensor[2].flatten()
        
        # Calculate correlations between residue types
        results["attr_hesitation_corr"] = float(np.corrcoef(attribution_pattern, hesitation_pattern)[0, 1])
        results["attr_collapse_corr"] = float(np.corrcoef(attribution_pattern, collapse_pattern)[0, 1])
        results["hesitation_collapse_corr"] = float(np.corrcoef(hesitation_pattern, collapse_pattern)[0, 1])
        
        # 5. Residue signature classification
        signature = self.classify_residue_signature()
        results["primary_signature"] = signature["primary_signature"]
        results["signature_confidence"] = signature["confidence"]
        results["signature_details"] = signature["details"]
        
        return results
        
    def classify_residue_signature(self) -> Dict[str, Any]:
        """
        Classify the residue pattern into a known signature.
        
        Returns:
            Dictionary with signature classification
        """
        # Calculate feature vector for classification
        features = []
        
        # Feature 1: Ratio of residue types
        total = np.sum(self.tensor) + 1e-10
        attr_ratio = np.sum(self.tensor[0]) / total
        hesit_ratio = np.sum(self.tensor[1]) / total
        collapse_ratio = np.sum(self.tensor[2]) / total
        features.extend([attr_ratio, hesit_ratio, collapse_ratio])
        
        # Feature 2: Layer distribution
        layer_dist = np.sum(self.tensor, axis=(1, 2, 3))
        features.extend(layer_dist / (np.sum(layer_dist) + 1e-10))
        
        # Feature 3: Depth progression
        depth_progression = np.sum(self.tensor, axis=(0, 1, 2))
        depth_slope = np.polyfit(np.arange(len(depth_progression)), depth_progression, 1)[0]
        features.append(depth_slope)
        
        # Define known signatures
        signatures = {
            "attribution_gap": np.array([0.7, 0.2, 0.1, 0.6, 0.3, 0.1, 0.2]),
            "phase_misalignment": np.array([0.2, 0.3, 0.5, 0.2, 0.2, 0.6, 0.8]),
            "boundary_erosion": np.array([0.4, 0.4, 0.2, 0.2, 0.6, 0.2, 0.1]),
            "temporal_instability": np.array([0.3, 0.6, 0.1, 0.4, 0.4, 0.2, -0.5]),
            "attractor_dissolution": np.array([0.2, 0.3, 0.5, 0.3, 0.3, 0.4, 0.3])
        }
        
        # Convert features to numpy array
        feature_vector = np.array(features)
        
        # Calculate distances to known signatures
        distances = {}
        for name, signature in signatures.items():
            # Ensure same length by padding
            max_len = max(len(feature_vector), len(signature))
            padded_feature = np.pad(feature_vector, (0, max_len - len(feature_vector)))
            padded_signature = np.pad(signature, (0, max_len - len(signature)))
            
            # Calculate cosine distance
            distances[name] = distance.cosine(padded_feature, padded_signature)
        
        # Find closest signature
        primary_signature = min(distances, key=distances.get)
        min_distance = distances[primary_signature]
        
        # Calculate confidence (inverse of distance)
        confidence = 1.0 / (1.0 + min_distance)
        
        # Return classification
        return {
            "primary_signature": primary_signature,
            "confidence": float(confidence),
            "details": {
                "distances": {k: float(v) for k, v in distances.items()},
                "feature_vector": feature_vector.tolist()
            }
        }
        
    def visualize_residue(self, 
                        output_path: Optional[str] = None,
                        show_plot: bool = True) -> None:
        """
        Visualize the residue tensor.
        
        Args:
            output_path: Optional path to save visualization
            show_plot: Whether to display the plot
        """
        fig = plt.figure(figsize=(15, 10))
        
        # 1. Heatmap of Attribution Voids
        ax1 = fig.add_subplot(231)
        attribution_heatmap = np.sum(self.tensor[0], axis=2)  # Sum over depths
        im1 = ax1.imshow(attribution_heatmap, cmap='Blues')
        ax1.set_title('Attribution Voids')
        ax1.set_xlabel('Token Position')
        ax1.set_ylabel('Layer')
        plt.colorbar(im1, ax=ax1)
        
        # 2. Heatmap of Token Hesitations
        ax2 = fig.add_subplot(232)
        hesitation_heatmap = np.sum(self.tensor[1], axis=0)  # Sum over layers
        im2 = ax2.imshow(hesitation_heatmap, cmap='Reds')
        ax2.set_title('Token Hesitations')
        ax2.set_xlabel('Token Position')
        ax2.set_ylabel('Recursive Depth')
        plt.colorbar(im2, ax=ax2)
        
        # 3. Heatmap of Recursive Collapses
        ax3 = fig.add_subplot(233)
        collapse_heatmap = np.sum(self.tensor[2], axis=1)  # Sum over tokens
        im3 = ax3.imshow(collapse_heatmap, cmap='Greens')
        ax3.set_title('Recursive Collapses')
        ax3.set_xlabel('Recursive Depth')
        ax3.set_ylabel('Layer')
        plt.colorbar(im3, ax=ax3)
        
        # 4. Line plot of residue by depth
        ax4 = fig.add_subplot(234)
        depth_sums = np.sum(self.tensor, axis=(1, 2))  # Sum over layers and tokens
        ax4.plot(range(self.depths), depth_sums[0], 'b-', label='Attribution Voids')
        ax4.plot(range(self.depths), depth_sums[1], 'r-', label='Token Hesitations')
        ax4.plot(range(self.depths), depth_sums[2], 'g-', label='Recursive Collapses')
        ax4.set_title('Residue by Recursive Depth')
        ax4.set_xlabel('Recursive Depth')
        ax4.set_ylabel('Total Residue')
        ax4.legend()
        
        # 5. Bar chart of residue by layer
        ax5 = fig.add_subplot(235)
        layer_sums = np.sum(self.tensor, axis=(2, 3))  # Sum over tokens and depths
        ax5.bar(range(self.layers), layer_sums[0], color='blue', alpha=0.3, label='Attribution Voids')
        ax5.bar(range(self.layers), layer_sums[1], bottom=layer_sums[0], color='red', alpha=0.3, label='Token Hesitations')
        ax5.bar(range(self.layers), layer_sums[2], bottom=layer_sums[0]+layer_sums[1], color='green', alpha=0.3, label='Recursive Collapses')
        ax5.set_title('Residue by Layer')
        ax5.set_xlabel('Layer')
        ax5.set_ylabel('Total Residue')
        ax5.legend()
        
        # 6. Pie chart of residue type distribution
        ax6 = fig.add_subplot(236)
        residue_totals = [np.sum(self.tensor[0]), np.sum(self.tensor[1]), np.sum(self.tensor[2])]
        ax6.pie(residue_totals, labels=['Attribution Voids', 'Token Hesitations', 'Recursive Collapses'],
                autopct='%1.1f%%', startangle=90)
        ax6.set_title('Residue Type Distribution')
        
        plt.tight_layout()
        
        # Save if output path provided
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            
        # Show if requested
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def reset(self) -> None:
        """Reset the residue tensor and all tracking."""
        self.initialize_tensor()
        self.attribution_voids = []
        self.token_hesitations = []
        self.recursive_collapses = []
        self.history = []
    
    def save(self, file_path: str) -> None:
        """
        Save the residue tensor and analysis to a file.
        
        Args:
            file_path: Path to save file
        """
        save_data = {
            "tensor": self.tensor,
            "attribution_voids": self.attribution_voids,
            "token_hesitations": self.token_hesitations,
            "recursive_collapses": self.recursive_collapses,
            "history": self.history,
            "config": self.config,
            "analysis": self.analyze_residue_pattern()
        }
        
        np.save(file_path, save_data, allow_pickle=True)
    
    def load(self, file_path: str) -> None:
        """
        Load residue tensor and analysis from a file.
        
        Args:
            file_path: Path to load file
        """
        load_data = np.load(file_path, allow_pickle=True).item()
        
        self.tensor = load_data["tensor"]
        self.attribution_voids = load_data["attribution_voids"]
        self.token_hesitations = load_data["token_hesitations"]
        self.recursive_collapses = load_data["recursive_collapses"]
        self.history = load_data["history"]
        self.config = load_data["config"]
        
        # Update dimensions
        self.layers = self.tensor.shape[1]
        self.tokens = self.tensor.shape[2]
        self.depths = self.tensor.shape[3]


# Example usage
if __name__ == "__main__":
    # Initialize tensor
    config = {
        "layers": 8,
        "tokens": 50,
        "depths": 5,
        "current_step": 0
    }
    residue_tensor = SymbolicResidueTensor(config)
    
    # Simulate recording some residue
    for layer in range(8):
        for depth in range(5):
            # More attribution voids in early layers, decreasing with depth
            void_magnitude = 0.9 * np.exp(-0.3 * layer) * np.exp(-0.2 * depth)
            if void_magnitude > 0.2:
                residue_tensor.record_attribution_void(
                    layer=layer,
                    token_position=10 + layer,
                    depth=depth,
                    magnitude=void_magnitude,
                    metadata={"source": "example"}
                )
    
    for token in range(10, 40):
        for depth in range(5):
            # Token hesitations increase with depth
            hesitation = 0.2 + 0.15 * depth
            oscillation = 0.1 + 0.1 * depth
            splitting = 0.1 * depth
            
            if token % 3 == 0:  # Periodic hesitations
                residue_tensor.record_token_hesitation(
                    token_position=token,
                    entropy=hesitation,
                    oscillation=oscillation,
                    splitting=splitting,
                    depth=depth,
                    metadata={"source": "example"}
                )
    
    # Record recursive collapse at depth 4
    residue_tensor.record_recursive_collapse(
        depth=4,
        coherence=0.3,
        collapse_threshold=0.7,
        severity=0.8,
        affected_circuits=[3, 4, 5],
        metadata={"source": "example", "trigger": "self-reference loop"}
    )
    
    # Analyze the residue pattern
    analysis = residue_tensor.analyze_residue_pattern()
    print("Residue Analysis:")
    for key, value in analysis.items():
        if not isinstance(value, dict):
            print(f"  {key}: {value}")
    
    # Visualize
    residue_tensor.visualize_residue(output_path="residue_visualization.png")
    
    print("\nPrimary Residue Signature:", analysis["primary_signature"])
    print("Signature Confidence:", analysis["signature_confidence"])
