import pyo
import tkinter as tk
from tkinter import ttk
import numpy as np

class SimpleSynthesizer:
    def __init__(self):
        # Initialize audio server
        self.server = pyo.Server().boot()
        self.server.start()
        
        # Create oscillator with default sine wave
        self.osc_types = ["Sine", "Square", "Saw", "Triangle"]
        self.active_osc = None
        self.oscillator = None  # Initialize to None first
        
        # Initialize filter before calling create_oscillator
        self.filter_types = ["Lowpass", "Highpass"]
        self.filter = pyo.Biquad(pyo.Sine(0), freq=1000, q=1, type=0)  # Use a dummy input initially
        
        # Now create the oscillator and connect it to the filter
        self.create_oscillator("Sine")
        
        # ADSR envelope
        self.envelope = pyo.Adsr(attack=0.1, decay=0.2, sustain=0.7, release=0.5, dur=0, mul=0.5)
        
        # LFO settings
        self.lfo = pyo.Sine(freq=1, mul=0.5, add=0.5)
        self.lfo_targets = ["None", "Pitch", "Amplitude", "Filter Cutoff"]
        self.lfo_target = "None"
        
        # Connect components
        self.output = self.filter * self.envelope
        self.output.out()
        
        # GUI setup
        self.setup_gui()
    
    def create_oscillator(self, osc_type):
        if self.active_osc:
            self.active_osc.stop()
        
        if osc_type == "Sine":
            self.oscillator = pyo.Sine(freq=440, mul=1)
        elif osc_type == "Square":
            self.oscillator = pyo.Square(freq=440, mul=1)
        elif osc_type == "Saw":
            self.oscillator = pyo.Saw(freq=440, mul=1)
        elif osc_type == "Triangle":
            # pyo doesn't have a Triangle class, use LFO instead
            self.oscillator = pyo.LFO(freq=440, type=3, mul=1)
        
        self.active_osc = self.oscillator
        
        # Update filter input
        self.filter.setInput(self.oscillator)
    
    def set_oscillator_type(self, osc_type):
        self.create_oscillator(osc_type)
    
    def set_frequency(self, freq):
        try:
            # Convert to float to ensure we're dealing with a numeric value
            freq_val = float(freq)
            # Set the frequency directly to the oscillator
            self.oscillator.setFreq(freq_val)
        except Exception as e:
            print(f"Error setting frequency: {e}")
    
    def set_adsr(self, attack, decay, sustain, release):
        try:
            # Update ADSR parameters
            self.envelope.setAttack(float(attack))
            self.envelope.setDecay(float(decay))
            self.envelope.setSustain(float(sustain))
            self.envelope.setRelease(float(release))
        except Exception as e:
            print(f"Error setting ADSR: {e}")
    
    def set_lfo_freq(self, freq):
        try:
            # Update LFO frequency
            self.lfo.setFreq(float(freq))
        except Exception as e:
            print(f"Error setting LFO frequency: {e}")
    
    def set_lfo_target(self, target):
        # Store current target
        prev_target = self.lfo_target
        self.lfo_target = target
        
        # Reset previous LFO modulation
        if prev_target == "Pitch" and target != "Pitch":
            # Reset oscillator frequency
            self.oscillator.setFreq(440)
        elif prev_target == "Amplitude" and target != "Amplitude":
            # Reset output amplitude
            self.output.setMul(0.5)
        elif prev_target == "Filter Cutoff" and target != "Filter Cutoff":
            # Reset filter cutoff
            self.filter.setFreq(1000)
        
        # Set up new LFO modulation
        try:
            if target == "None":
                self.lfo.stop()
            elif target == "Pitch":
                # Use a lookup table for pitch modulation
                self.lfo.play()
                pitch_mod = pyo.SigTo(440, time=0.01, init=440)
                
                def update_pitch():
                    # Scale pitch between 0.5x and 1.5x the base frequency
                    new_freq = 440 * (0.5 + self.lfo.get())
                    pitch_mod.setValue(new_freq)
                
                # Call update 20 times per second
                pat = pyo.Pattern(function=update_pitch, time=0.05).play()
                self.oscillator.setFreq(pitch_mod)
                
            elif target == "Amplitude":
                self.lfo.play()
                # Create a SigTo for smooth transitions
                amp_mod = pyo.SigTo(0.5, time=0.01, init=0.5)
                
                def update_amp():
                    amp_mod.setValue(self.lfo.get())
                
                # Call update 20 times per second
                pat = pyo.Pattern(function=update_amp, time=0.05).play()
                self.output.setMul(amp_mod)
                
            elif target == "Filter Cutoff":
                self.lfo.play()
                # Create a SigTo for smooth transitions
                filter_mod = pyo.SigTo(1000, time=0.01, init=1000)
                
                def update_filter():
                    # Scale filter cutoff between 500 and 4500 Hz
                    new_cutoff = 500 + self.lfo.get() * 4000
                    filter_mod.setValue(new_cutoff)
                
                # Call update 20 times per second
                pat = pyo.Pattern(function=update_filter, time=0.05).play()
                self.filter.setFreq(filter_mod)
        except Exception as e:
            print(f"Error setting LFO target: {e}")
    
    def set_filter_type(self, filter_type):
        try:
            if filter_type == "Lowpass":
                self.filter.setType(0)
            elif filter_type == "Highpass":
                self.filter.setType(1)
        except Exception as e:
            print(f"Error setting filter type: {e}")
    
    def set_filter_cutoff(self, cutoff):
        try:
            # Set filter cutoff
            self.filter.setFreq(float(cutoff))
        except Exception as e:
            print(f"Error setting filter cutoff: {e}")
    
    def set_filter_resonance(self, resonance):
        try:
            # Set filter Q (resonance)
            self.filter.setQ(float(resonance))
        except Exception as e:
            print(f"Error setting filter resonance: {e}")
    
    def note_on(self):
        # Play the envelope
        self.envelope.play()
    
    def note_off(self):
        # Stop the envelope (trigger release phase)
        self.envelope.stop()
    
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Simple Synthesizer")
        self.root.geometry("600x500")
        
        # Create tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Oscillator tab
        osc_frame = ttk.Frame(notebook)
        notebook.add(osc_frame, text="Oscillator")
        
        ttk.Label(osc_frame, text="Oscillator Type:").grid(row=0, column=0, padx=10, pady=10)
        osc_type = ttk.Combobox(osc_frame, values=self.osc_types)
        osc_type.current(0)
        osc_type.grid(row=0, column=1, padx=10, pady=10)
        osc_type.bind("<<ComboboxSelected>>", lambda e: self.set_oscillator_type(osc_type.get()))
        
        ttk.Label(osc_frame, text="Frequency (Hz):").grid(row=1, column=0, padx=10, pady=10)
        freq_slider = ttk.Scale(osc_frame, from_=20, to=2000, orient=tk.HORIZONTAL, length=200)
        freq_slider.set(440)
        freq_slider.grid(row=1, column=1, padx=10, pady=10)
        # Update the binding to use ButtonRelease instead of Motion for better performance
        freq_slider.bind("<ButtonRelease-1>", lambda e: self.set_frequency(freq_slider.get()))
        
        self.freq_label = ttk.Label(osc_frame, text="440")
        self.freq_label.grid(row=1, column=2)
        freq_slider.bind("<Motion>", lambda e: self.freq_label.configure(text=f"{int(freq_slider.get())}"))
        
        # ADSR tab
        adsr_frame = ttk.Frame(notebook)
        notebook.add(adsr_frame, text="ADSR")
        
        # Attack
        ttk.Label(adsr_frame, text="Attack (s):").grid(row=0, column=0, padx=10, pady=10)
        attack_slider = ttk.Scale(adsr_frame, from_=0.01, to=2.0, orient=tk.HORIZONTAL, length=200)
        attack_slider.set(0.1)
        attack_slider.grid(row=0, column=1, padx=10, pady=10)
        self.attack_label = ttk.Label(adsr_frame, text="0.1")
        self.attack_label.grid(row=0, column=2)
        attack_slider.bind("<ButtonRelease-1>", lambda e: self.set_adsr(attack_slider.get(), 
                                                               decay_slider.get(), 
                                                               sustain_slider.get(), 
                                                               release_slider.get()))
        attack_slider.bind("<Motion>", lambda e: self.attack_label.configure(text=f"{attack_slider.get():.2f}"))
        
        # Decay
        ttk.Label(adsr_frame, text="Decay (s):").grid(row=1, column=0, padx=10, pady=10)
        decay_slider = ttk.Scale(adsr_frame, from_=0.01, to=2.0, orient=tk.HORIZONTAL, length=200)
        decay_slider.set(0.2)
        decay_slider.grid(row=1, column=1, padx=10, pady=10)
        self.decay_label = ttk.Label(adsr_frame, text="0.2")
        self.decay_label.grid(row=1, column=2)
        decay_slider.bind("<ButtonRelease-1>", lambda e: self.set_adsr(attack_slider.get(), 
                                                               decay_slider.get(), 
                                                               sustain_slider.get(), 
                                                               release_slider.get()))
        decay_slider.bind("<Motion>", lambda e: self.decay_label.configure(text=f"{decay_slider.get():.2f}"))
        
        # Sustain
        ttk.Label(adsr_frame, text="Sustain:").grid(row=2, column=0, padx=10, pady=10)
        sustain_slider = ttk.Scale(adsr_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200)
        sustain_slider.set(0.7)
        sustain_slider.grid(row=2, column=1, padx=10, pady=10)
        self.sustain_label = ttk.Label(adsr_frame, text="0.7")
        self.sustain_label.grid(row=2, column=2)
        sustain_slider.bind("<ButtonRelease-1>", lambda e: self.set_adsr(attack_slider.get(), 
                                                                decay_slider.get(), 
                                                                sustain_slider.get(), 
                                                                release_slider.get()))
        sustain_slider.bind("<Motion>", lambda e: self.sustain_label.configure(text=f"{sustain_slider.get():.2f}"))
        
        # Release
        ttk.Label(adsr_frame, text="Release (s):").grid(row=3, column=0, padx=10, pady=10)
        release_slider = ttk.Scale(adsr_frame, from_=0.01, to=5.0, orient=tk.HORIZONTAL, length=200)
        release_slider.set(0.5)
        release_slider.grid(row=3, column=1, padx=10, pady=10)
        self.release_label = ttk.Label(adsr_frame, text="0.5")
        self.release_label.grid(row=3, column=2)
        release_slider.bind("<ButtonRelease-1>", lambda e: self.set_adsr(attack_slider.get(), 
                                                                decay_slider.get(), 
                                                                sustain_slider.get(), 
                                                                release_slider.get()))
        release_slider.bind("<Motion>", lambda e: self.release_label.configure(text=f"{release_slider.get():.2f}"))
        
        # LFO tab
        lfo_frame = ttk.Frame(notebook)
        notebook.add(lfo_frame, text="LFO")
        
        ttk.Label(lfo_frame, text="LFO Target:").grid(row=0, column=0, padx=10, pady=10)
        lfo_target = ttk.Combobox(lfo_frame, values=self.lfo_targets)
        lfo_target.current(0)
        lfo_target.grid(row=0, column=1, padx=10, pady=10)
        lfo_target.bind("<<ComboboxSelected>>", lambda e: self.set_lfo_target(lfo_target.get()))
        
        ttk.Label(lfo_frame, text="LFO Frequency (Hz):").grid(row=1, column=0, padx=10, pady=10)
        lfo_freq_slider = ttk.Scale(lfo_frame, from_=0.1, to=20, orient=tk.HORIZONTAL, length=200)
        lfo_freq_slider.set(1)
        lfo_freq_slider.grid(row=1, column=1, padx=10, pady=10)
        self.lfo_freq_label = ttk.Label(lfo_frame, text="1.0")
        self.lfo_freq_label.grid(row=1, column=2)
        lfo_freq_slider.bind("<ButtonRelease-1>", lambda e: self.set_lfo_freq(lfo_freq_slider.get()))
        lfo_freq_slider.bind("<Motion>", lambda e: self.lfo_freq_label.configure(text=f"{lfo_freq_slider.get():.2f}"))
        
        # Filter tab
        filter_frame = ttk.Frame(notebook)
        notebook.add(filter_frame, text="Filter")
        
        ttk.Label(filter_frame, text="Filter Type:").grid(row=0, column=0, padx=10, pady=10)
        filter_type = ttk.Combobox(filter_frame, values=self.filter_types)
        filter_type.current(0)
        filter_type.grid(row=0, column=1, padx=10, pady=10)
        filter_type.bind("<<ComboboxSelected>>", lambda e: self.set_filter_type(filter_type.get()))
        
        ttk.Label(filter_frame, text="Cutoff Frequency (Hz):").grid(row=1, column=0, padx=10, pady=10)
        cutoff_slider = ttk.Scale(filter_frame, from_=20, to=20000, orient=tk.HORIZONTAL, length=200)
        cutoff_slider.set(1000)
        cutoff_slider.grid(row=1, column=1, padx=10, pady=10)
        self.cutoff_label = ttk.Label(filter_frame, text="1000")
        self.cutoff_label.grid(row=1, column=2)
        cutoff_slider.bind("<ButtonRelease-1>", lambda e: self.set_filter_cutoff(cutoff_slider.get()))
        cutoff_slider.bind("<Motion>", lambda e: self.cutoff_label.configure(text=f"{int(cutoff_slider.get())}"))
        
        ttk.Label(filter_frame, text="Resonance:").grid(row=2, column=0, padx=10, pady=10)
        resonance_slider = ttk.Scale(filter_frame, from_=0.1, to=10, orient=tk.HORIZONTAL, length=200)
        resonance_slider.set(1)
        resonance_slider.grid(row=2, column=1, padx=10, pady=10)
        self.resonance_label = ttk.Label(filter_frame, text="1.0")
        self.resonance_label.grid(row=2, column=2)
        resonance_slider.bind("<ButtonRelease-1>", lambda e: self.set_filter_resonance(resonance_slider.get()))
        resonance_slider.bind("<Motion>", lambda e: self.resonance_label.configure(text=f"{resonance_slider.get():.2f}"))
        
        # Play area
        play_frame = ttk.Frame(self.root)
        play_frame.pack(fill=tk.X, padx=10, pady=10)
        
        play_button = ttk.Button(play_frame, text="Play Note")
        play_button.pack(pady=10)
        play_button.bind("<ButtonPress>", lambda e: self.note_on())
        play_button.bind("<ButtonRelease>", lambda e: self.note_off())
        
        # Keyboard shortcuts
        self.root.bind("<KeyPress-space>", lambda e: self.note_on())
        self.root.bind("<KeyRelease-space>", lambda e: self.note_off())
        
    def run(self):
        self.root.mainloop()
        # Clean up resources before closing
        self.server.stop()
        print("Synthesizer stopped")


# Run the synthesizer if this script is executed directly
if __name__ == "__main__":
    synth = SimpleSynthesizer()
    synth.run()
