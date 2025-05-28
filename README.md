Here's a complete `README.md` file you can use for your GitHub repository:

---

# Houdini Network Cleaner Tool

A powerful utility for cleaning up your Houdini scene networks. This tool identifies and safely removes **unused** and **bypassed** nodes to help maintain clean, efficient node networks — all with a visual preview and an intuitive PyQt-based GUI.

---

## ✨ Features

* 🔍 **Preview Mode** – Highlights nodes (in bright magenta) that can be deleted.
* ⚡ **Multithreaded Analysis** – Keeps Houdini responsive during node scanning.
* 🧼 **Safe Deletion** – Only deletes nodes confirmed unused or bypassed.
* 🎨 **Visual Highlighting** – Temporarily changes node colors for clarity.
* 🖼️ **PyQt GUI** – Clean, easy-to-use interface for managing cleanup operations.
* 🔁 **Color Restore** – Safely restores node colors if preview is canceled.

---

## 🧠 How It Works

* **Unused Nodes**: No outputs, not referenced, and no active display/render/template flags.
* **Bypassed Nodes**: Explicitly bypassed by the user.
* Nodes are analyzed in a background thread, and if marked for deletion, are **highlighted**.
* You can review the nodes and safely delete them, or cancel to restore their original colors.

---

## 🖥️ Usage

### Inside Houdini:

1. Open a Houdini Python Panel.

2. Run the script to initialize the GUI:

   ```python
   cleaner = HoudiniNetworkCleaner()
   gui = CleanerGUI(cleaner)
   gui.show()
   ```

3. Use the interface:

   * **Preview Nodes for Deletion**: Scans the current network.
   * **Execute Deletion**: Removes highlighted nodes.
   * **Clear Preview**: Cancels and restores colors.

---

## 📸 Preview

> *Magenta nodes represent unused/bypassed nodes ready for deletion.*


## 💬 Console Output Example

```plaintext
==================================================
PREVIEW MODE - 12 nodes highlighted for deletion:
==================================================
📍 Unused nodes (7):
    - scatter1
    - vdbsmooth2
    ...
🚫 Bypassed nodes (5):
    - polyextrude2
    - normal3
    ...
💡 Nodes are highlighted in BRIGHT PINK/MAGENTA color
📝 Use execute_deletion() to delete highlighted nodes
📝 Use clear_preview() to cancel and restore colors
==================================================
```

---

## 👨‍💻 Author

Developed by [waveWhirlVfx](https://github.com/waveWhirlVfx)
If you use this tool in your production or projects, feel free to ⭐ the repo!

---

## 📜 License

This project is licensed under the MIT License.
See the [LICENSE](LICENSE) file for details.
