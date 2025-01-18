import React, { useEffect, useState, useRef } from "react";
import { AppBar, Toolbar, Button, Switch } from "@mui/material";

import { createRoot } from 'react-dom';
import {
    colors,
    CssBaseline,
    ThemeProvider,
    Typography,
    Container,
    createTheme,
    Box,
    SvgIcon,
    Link,
} from '@mui/material';

const theme = createTheme({
    cssVariables: true,
    palette: {
        primary: {
            main: '#556cd6',
        },
        secondary: {
            main: '#19857b',
        },
        error: {
            main: colors.red.A400,
        },
    },
});

function App() {
    const canvasRef = useRef(null);
    const [threeModule, setThreeModule] = useState(null);

    useEffect(() => {
        if (canvasRef.current && !threeModule) {
            import("./app.js").then((module) => {
                setThreeModule(module);
            });
        }
    }, [canvasRef, threeModule]);

    const [showSettings, setShowSettings] = useState(false);
    const [movementSpeed, setMovementSpeed] = useState(18);
    const [movementDelay, setMovementDelay] = useState(40);
    const [showColorPicker, setShowColorPicker] = useState(false);

    return (
        <div style={{ width: "100vw", height: "100vh", overflow: "hidden" }}>
            <div style={{ width: "100%", height: "100%" }}>
                <canvas id="viewport" tabindex="0"  ref={canvasRef} style={{ width: "100%", height: "100%" }}></canvas>
            </div>

            <AppBar position="absolute" sx={{ bottom: 0, top: "auto", background: "#11111133" }}>
                <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
                    <Box sx={{ display: "flex", gap: "10px" }}>
                        <Button variant="contained" onClick={() => setShowColorPicker(!showColorPicker)}>
                            <span className="material-icons">color_lens</span>
                        </Button>
                        <Button variant="contained" onClick={() => threeModule?.toggleDayNight?.()}>
                            <span className="material-icons">wb_sunny</span>
                        </Button>
                        <Button variant="contained" onClick={() => threeModule?.startMeasure?.()}>
                            <span className="material-icons">straighten</span>
                        </Button>
                    </Box>
                    <Box sx={{ display: "flex", gap: "10px" }}>
                        <Button variant="contained" onClick={() => threeModule?.toggleDollhouseView?.()}>
                            <span className="material-icons">fullscreen</span>
                        </Button>
                        <Button variant="contained" onClick={() => threeModule?.screenshot?.()}>
                            <span className="material-icons">photo_camera</span>
                        </Button>
                        <Button variant="contained" onClick={() => threeModule?.saveCameraAndIndexToURL?.()}>
                            <span className="material-icons">share</span>
                        </Button>
                        <Button variant="contained" onClick={() => setShowSettings(!showSettings)}>
                            <span className="material-icons">settings</span>
                        </Button>
                        
                    </Box>
                </Toolbar>
            </AppBar>

            {/* Settings Dialog */}
            {showSettings && (
                <div
                    style={{
                        position: "absolute",
                        bottom: 80,
                        right: 10,
                        background: "white",
                        padding: 20,
                        borderRadius: 5,
                        boxShadow: "0 0 10px rgba(0,0,0,0.5)",
                    }}
                >
                    <Typography variant="h6">Settings</Typography>
                    <Box sx={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "10px" }}>
                        <Typography>Movement Speed</Typography>

                        <Box sx={{ display: "flex", flexDirection: "row", gap: "10px" }}>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={movementSpeed}
                                onChange={(e) => {
                                    const newSpeed = parseFloat(e.target.value);  // get new value from slider
                                    setMovementSpeed(newSpeed);  // update state first
                                    threeModule?.setMovementSpeed(newSpeed / 500);
                                }}
                            />
                            <Typography>{Math.round(movementSpeed)}</Typography>
                        </Box>

                        <Typography>Movement Delay</Typography>
                        <Box sx={{ display: "flex", flexDirection: "row", gap: "10px" }}>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={movementDelay}
                                onChange={(e) => {
                                    const newDelay = parseFloat(e.target.value);  // get new value from slider
                                    setMovementDelay(newDelay);  // update state first
                                    threeModule?.setMovementDelay(newDelay);
                                }}
                            />
                            <Typography>{Math.round(movementDelay)}</Typography>
                        </Box>

                        <Button variant="contained" onClick={() => setShowSettings(false)}>
                            Close
                        </Button>
                    </Box>
                </div>
            )}

            {/* Color Picker Dialog */}
            {showColorPicker && (
                <div
                    style={{
                        position: "absolute",
                        bottom: 80,
                        left: 10,
                        background: "white",
                        padding: 20,
                        borderRadius: 5,
                        boxShadow: "0 0 10px rgba(0,0,0,0.5)",
                    }}
                >
                    <Typography variant="h6">Color Picker</Typography>
                    <Box sx={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "10px" }}>
                        <Typography>Floor</Typography>
                        <select onChange={(e) => threeModule?.setFloorColor(e.target.value)}>
                            <option value="0">Base</option>
                            <option value="1">Darker</option>
                            <option value="2">Lighter</option>
                        </select>

                        <Typography>Sofa</Typography>
                        <select onChange={(e) => threeModule?.setSofaColor(e.target.value)}>
                            <option value="0">Base</option>
                            <option value="1">Blue</option>
                            <option value="2">Pink</option>
                        </select>

                        <Button variant="contained" onClick={() => setShowColorPicker(false)}>
                            Close
                        </Button>
                    </Box>
                </div>
            )}

            <div
                style={{
                    position: "absolute",
                    top: 10,
                    right: 10,
                    width: 100,
                    height: 100,
                    background: "rgba(255,255,255,0.5)",
                    borderRadius: 5,
                    textAlign: "center",
                    padding: 5,
                }}
            ></div>
        </div>
    );
}

const root = createRoot(document.getElementById('overlay'));
root.render(
    <ThemeProvider theme={theme}>
        { }
        <CssBaseline />
        <App />
    </ThemeProvider>,
);