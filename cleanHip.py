# Houdini Network Cleaner Tool with Threading and Visual Preview and GUI
# This script cleans the current network by removing unused and bypassed nodes
# Features: Threading for performance, Visual preview with color highlighting, and a PyQt-based GUI

import hou
import threading
import time
from PySide2 import QtWidgets, QtCore, QtGui

class HoudiniNetworkCleaner:
    def __init__(self):
        self.preview_color = hou.Color(1.0, 0.2, 0.8)  # Bright pink/magenta - unique color
        self.original_colors = {}  # Store original node colors
        self.nodes_to_delete = []
        self.is_preview_active = False
        
    def get_current_network(self):
        """Get the current network context"""
        desktop = hou.ui.curDesktop()
        network_editor = desktop.paneTabOfType(hou.paneTabType.NetworkEditor)
        
        if network_editor:
            return network_editor.pwd()
        else:
            return hou.node("/obj")

    def get_unique_preview_color(self, network):
        """Find a unique color that's not used by existing nodes"""
        used_colors = set()
        
        # Collect all existing node colors
        for node in network.children():
            try:
                color = node.color()
                used_colors.add((round(color.rgb()[0], 2), round(color.rgb()[1], 2), round(color.rgb()[2], 2)))
            except:
                pass
        
        # Try different unique colors
        unique_colors = [
            hou.Color(1.0, 0.2, 0.8),  # Bright magenta
            hou.Color(0.0, 1.0, 1.0),  # Cyan
            hou.Color(1.0, 0.5, 0.0),  # Orange
            hou.Color(0.5, 0.0, 1.0),  # Purple
            hou.Color(1.0, 1.0, 0.0),  # Yellow
        ]
        
        for color in unique_colors:
            color_tuple = (round(color.rgb()[0], 2), round(color.rgb()[1], 2), round(color.rgb()[2], 2))
            if color_tuple not in used_colors:
                return color
        
        # Fallback to bright magenta if all colors are used
        return hou.Color(1.0, 0.2, 0.8)

    def find_unused_nodes(self, network):
        """Find nodes that are not connected to any outputs and have no dependencies"""
        unused_nodes = []
        all_nodes = network.children()
        
        for node in all_nodes:
            try:
                # Skip if node has a lock flag
                if hasattr(node, 'isHardLocked') and node.isHardLocked():
                    continue
                elif hasattr(node, 'isLocked') and node.isLocked():
                    continue
                
                # Skip special nodes
                if node.type().name() in ['output', 'rop_geometry', 'rop_alembic', 'null']:
                    continue
                
                # Check if node has any outputs connected
                has_output_connections = False
                for output in node.outputs():
                    if output.outputConnections():
                        has_output_connections = True
                        break
                
                # Check if node is referenced by other nodes
                is_referenced = len(node.dependents()) > 0
                
                # Check if node has display or render flag
                has_flags = False
                if hasattr(node, 'isDisplayFlagSet') and node.isDisplayFlagSet():
                    has_flags = True
                elif hasattr(node, 'isRenderFlagSet') and node.isRenderFlagSet():
                    has_flags = True
                elif hasattr(node, 'isTemplateFlagSet') and node.isTemplateFlagSet():
                    has_flags = True
                
                # Node is unused if it has no output connections, no dependents, and no flags
                if not has_output_connections and not is_referenced and not has_flags:
                    unused_nodes.append(node)
                    
            except Exception as e:
                print(f"Error checking node {node.name()}: {str(e)}")
                continue
        
        return unused_nodes

    def find_bypassed_nodes(self, network):
        """Find nodes that are bypassed"""
        bypassed_nodes = []
        all_nodes = network.children()
        
        for node in all_nodes:
            try:
                # Skip if node has a lock flag
                if hasattr(node, 'isHardLocked') and node.isHardLocked():
                    continue
                elif hasattr(node, 'isLocked') and node.isLocked():
                    continue
                
                # Check if node is bypassed
                if hasattr(node, 'isBypassed') and node.isBypassed():
                    bypassed_nodes.append(node)
                    
            except Exception as e:
                print(f"Error checking bypass on node {node.name()}: {str(e)}")
                continue
        
        return bypassed_nodes

    def highlight_nodes_for_deletion(self, nodes):
        """Highlight nodes that will be deleted with a unique color"""
        if not nodes:
            return
            
        # Get unique color
        network = self.get_current_network()
        self.preview_color = self.get_unique_preview_color(network)
        
        # Store original colors and apply preview color
        for node in nodes:
            try:
                self.original_colors[node.path()] = node.color()
                node.setColor(self.preview_color)
            except Exception as e:
                print(f"Error setting color for node {node.name()}: {str(e)}")
        
        self.is_preview_active = True
        print(f"Highlighted {len(nodes)} nodes for deletion in bright pink/magenta")

    def restore_original_colors(self):
        """Restore original node colors"""
        if not self.is_preview_active and not self.original_colors: # Ensure only restore if preview was active or colors stored
            return
            
        for node_path, original_color in list(self.original_colors.items()): # Use list() to allow modification during iteration
            try:
                node = hou.node(node_path)
                if node:
                    node.setColor(original_color)
                del self.original_colors[node_path] # Remove after restoring
            except Exception as e:
                print(f"Error restoring color for node {node_path}: {str(e)}")
        
        self.original_colors.clear()
        self.is_preview_active = False
        print("Restored original node colors")

    def safe_delete_nodes_immediate(self, nodes):
        """Delete nodes immediately on main thread"""
        deleted_count = 0
        failed_nodes = []
        
        # Always restore colors before deleting to ensure clean state
        self.restore_original_colors()

        for node in nodes:
            try:
                node_name = node.name()
                node_path = node.path()
                                
                node.destroy()
                deleted_count += 1
                print(f"Deleted: {node_name}")
                
            except Exception as e:
                failed_nodes.append((node.name(), str(e)))
                print(f"Failed to delete {node.name()}: {str(e)}")
        
        return deleted_count, failed_nodes

    def preview_cleanup(self, update_gui_callback=None):
        """Preview what nodes would be deleted with visual highlighting"""
        current_network = self.get_current_network()
        if not current_network:
            if update_gui_callback:
                update_gui_callback("Error: Could not determine current network", 0, 0)
            hou.ui.displayMessage("Error: Could not determine current network")
            return
            
        print(f"Analyzing network: {current_network.path()}")
        
        # Clear any existing preview
        self.restore_original_colors()
        
        def analysis_worker():
            try:
                unused_nodes = self.find_unused_nodes(current_network)
                bypassed_nodes = self.find_bypassed_nodes(current_network)
                all_nodes = list(set(unused_nodes + bypassed_nodes))
                
                # Update on main thread
                hou.ui.addEventLoopCallback(lambda: self.show_preview_results(all_nodes, unused_nodes, bypassed_nodes, update_gui_callback))
                
            except Exception as e:
                error_msg = f"Error during analysis: {str(e)}"
                if update_gui_callback:
                    hou.ui.addEventLoopCallback(lambda: update_gui_callback(error_msg, 0, 0))
                hou.ui.addEventLoopCallback(lambda: hou.ui.displayMessage(error_msg))
        
        # Run analysis in separate thread
        thread = threading.Thread(target=analysis_worker)
        thread.daemon = True
        thread.start()

    def show_preview_results(self, all_nodes, unused_nodes, bypassed_nodes, update_gui_callback=None):
        """Show preview results on main thread"""
        self.nodes_to_delete = all_nodes
        
        if not all_nodes:
            print("No nodes would be deleted.")
            if update_gui_callback:
                update_gui_callback("No nodes found for deletion.", 0, 0)
            return
            
        # Highlight nodes visually
        self.highlight_nodes_for_deletion(all_nodes)
        
        # Print detailed results to console instead of dialog
        console_output = f"\n{'='*50}\n"
        console_output += f"PREVIEW MODE - {len(all_nodes)} nodes highlighted for deletion:\n"
        console_output += f"{'='*50}\n"
        console_output += f"📍 Unused nodes ({len(unused_nodes)}):\n"
        for i, node in enumerate(unused_nodes):
            if i < 10:  # Show first 10
                console_output += f"    - {node.name()}\n"
            elif i == 10:
                console_output += f"    ... and {len(unused_nodes) - 10} more unused nodes\n"
                break
        
        console_output += f"\n🚫 Bypassed nodes ({len(bypassed_nodes)}):\n"
        for i, node in enumerate(bypassed_nodes):
            if i < 10:  # Show first 10
                console_output += f"    - {node.name()}\n"
            elif i == 10:
                console_output += f"    ... and {len(bypassed_nodes) - 10} more bypassed nodes\n"
                break
        
        console_output += f"\n💡 Nodes are highlighted in BRIGHT PINK/MAGENTA color\n"
        console_output += f"📝 Use execute_deletion() to delete highlighted nodes\n"
        console_output += f"📝 Use clear_preview() to cancel and restore colors\n"
        console_output += f"{'='*50}\n"
        print(console_output)

        if update_gui_callback:
            update_gui_callback(f"Found {len(all_nodes)} nodes. Highlighted in bright pink/magenta.", len(unused_nodes), len(bypassed_nodes))

    def execute_deletion(self, update_gui_callback=None):
        """Execute the deletion of highlighted nodes"""
        if not self.nodes_to_delete:
            print("❌ No nodes selected for deletion.")
            if update_gui_callback:
                update_gui_callback("No nodes to delete. Run Preview first.", 0, 0)
            return
            
        print(f"\n🗑️  Starting deletion of {len(self.nodes_to_delete)} nodes...")
        
        # Delete immediately on main thread
        deleted_count, failed_nodes = self.safe_delete_nodes_immediate(self.nodes_to_delete)
        
        # Show results in console
        console_output = f"\n{'='*50}\n"
        console_output += f"✅ DELETION COMPLETED\n"
        console_output += f"{'='*50}\n"
        console_output += f"Successfully deleted: {deleted_count} nodes\n"
        
        if failed_nodes:
            console_output += f"❌ Failed to delete: {len(failed_nodes)} nodes\n"
            for name, error in failed_nodes[:5]:
                console_output += f"    - {name}: {error}\n"
            if len(failed_nodes) > 5:
                console_output += f"    ... and {len(failed_nodes) - 5} more failures\n"
        
        console_output += f"{'='*50}\n"
        print(console_output)
            
        # Clear preview state
        self.nodes_to_delete = []
        self.is_preview_active = False

        if update_gui_callback:
            update_gui_callback(f"Deleted {deleted_count} nodes. Failed: {len(failed_nodes)}.", 0, 0)

    def clear_preview(self, update_gui_callback=None):
        """Clear visual preview and restore original colors"""
        self.restore_original_colors()
        self.nodes_to_delete = []
        if update_gui_callback:
            update_gui_callback("Preview cleared. Colors restored.", 0, 0)
        print("Preview cleared and colors restored.")

class CleanerGUI(QtWidgets.QWidget):
    def __init__(self, cleaner_instance):
        super().__init__()
        self.cleaner = cleaner_instance
        self.setWindowTitle("Houdini Network Cleaner")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) # Keep window on top
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Title
        title_label = QtWidgets.QLabel("Houdini Network Cleaner")
        title_label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)
        
        layout.addSpacing(10)

        # Preview Section
        preview_group = QtWidgets.QGroupBox("Preview & Execute")
        preview_layout = QtWidgets.QVBoxLayout()

        preview_button = QtWidgets.QPushButton("Preview Nodes for Deletion")
        preview_button.setToolTip("Highlights unused and bypassed nodes in the current network.")
        preview_button.clicked.connect(self.run_preview_cleanup)
        preview_layout.addWidget(preview_button)

        self.status_label = QtWidgets.QLabel("Status: Ready to analyze.")
        preview_layout.addWidget(self.status_label)
        
        self.unused_count_label = QtWidgets.QLabel("Unused Nodes: 0")
        preview_layout.addWidget(self.unused_count_label)
        
        self.bypassed_count_label = QtWidgets.QLabel("Bypassed Nodes: 0")
        preview_layout.addWidget(self.bypassed_count_label)

        execute_button = QtWidgets.QPushButton("Execute Deletion")
        execute_button.setToolTip("Deletes the currently highlighted nodes.")
        execute_button.clicked.connect(self.run_execute_deletion)
        preview_layout.addWidget(execute_button)

        clear_button = QtWidgets.QPushButton("Clear Preview")
        clear_button.setToolTip("Restores original colors and clears the preview selection.")
        clear_button.clicked.connect(self.run_clear_preview)
        preview_layout.addWidget(clear_button)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        layout.addSpacing(15)
        
        # Info and Credits
        info_label = QtWidgets.QLabel(
            "This tool helps clean up your Houdini networks by identifying "
            "and removing unused or bypassed nodes. \n"
            "Nodes to be deleted are highlighted in **bright pink/magenta** for visual confirmation."
        )
        info_label.setWordWrap(True)
        info_label.setTextFormat(QtCore.Qt.RichText)
        info_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        layout.addWidget(info_label)

        self.setLayout(layout)

    def update_gui_status(self, message, unused_count=None, bypassed_count=None):
        self.status_label.setText(f"Status: {message}")
        if unused_count is not None:
            self.unused_count_label.setText(f"Unused Nodes: {unused_count}")
        if bypassed_count is not None:
            self.bypassed_count_label.setText(f"Bypassed Nodes: {bypassed_count}")

    def run_preview_cleanup(self):
        self.update_gui_status("Analyzing network... Please wait.")
        self.cleaner.preview_cleanup(self.update_gui_status)

    def run_execute_deletion(self):
        confirm = hou.ui.displayMessage(
            "Are you sure you want to delete the highlighted nodes?",
            buttons=("Yes", "No"),
            title="Confirm Deletion"
        )
        if confirm == 0:  # "Yes" button
            self.update_gui_status("Deleting nodes...")
            self.cleaner.execute_deletion(self.update_gui_status)
        else:
            self.update_gui_status("Deletion cancelled.")

    def run_clear_preview(self):
        self.cleaner.clear_preview(self.update_gui_status)


# Global instance of the cleaner logic
cleaner_instance = HoudiniNetworkCleaner()

# Function to launch the GUI
def launch_cleaner_gui():
    global cleaner_window
    try:
        # Close any existing instance of the GUI to prevent multiple windows
        if 'cleaner_window' in globals() and cleaner_window.isVisible():
            cleaner_window.close()
            cleaner_window.deleteLater()
    except:
        pass # Ignore errors if window doesn't exist or is already closed

    cleaner_window = CleanerGUI(cleaner_instance)
    cleaner_window.show()

# Main execution for testing or direct launch
launch_cleaner_gui()
