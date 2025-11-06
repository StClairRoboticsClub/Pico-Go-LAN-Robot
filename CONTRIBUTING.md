# Contributing to Pico-Go LAN Robot

Thank you for your interest in contributing to the Pico-Go LAN Robot project! This is an educational project from the St. Clair College Robotics Club.

## 🤝 How to Contribute

### Reporting Bugs

Found a bug? Please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, MicroPython version)
- Serial output or error messages

### Suggesting Enhancements

Have an idea? Open an issue describing:
- The feature you'd like to see
- Use case and benefits
- Possible implementation approach

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**: `git commit -m "Add: feature description"`
6. **Push to your fork**: `git push origin feature/your-feature`
7. **Open a Pull Request**

## 📋 Development Guidelines

### Code Style

**Python (Controller)**:
- Follow PEP 8
- Use type hints where applicable
- Document all functions with docstrings
- Keep functions focused and small

**MicroPython (Firmware)**:
- Use clear variable names
- Comment complex logic
- Keep memory usage minimal
- Test on actual hardware

### Commit Messages

Use conventional commits:
- `Add: new feature`
- `Fix: bug description`
- `Docs: documentation update`
- `Refactor: code improvement`
- `Test: add or update tests`

### Testing

Before submitting:
- [ ] Test firmware on actual Pico W
- [ ] Test controller with Xbox controller
- [ ] Verify network connectivity
- [ ] Check for no regression in existing features
- [ ] Update documentation if needed

## 🎯 Areas for Contribution

### High Priority
- Additional sensor integration (ultrasonic, line following)
- Telemetry dashboard (web interface)
- Unit tests for firmware modules
- Integration tests for full system
- Video tutorials

### Medium Priority
- Alternative controller support (PS4, keyboard)
- ROS2 integration
- Additional LCD themes/layouts
- Performance optimizations
- Power consumption monitoring

### Documentation
- Translation to other languages
- Video assembly guide
- Troubleshooting scenarios
- Competition use cases
- Educational curriculum materials

## 🏗️ Project Structure

```
firmware/     - MicroPython code for Pico W
controller/   - Python controller application
docs/         - Documentation
schematics/   - Hardware diagrams
```

## 🧪 Testing Checklist

### For Firmware Changes
- [ ] Syntax check (no MicroPython errors)
- [ ] Test on actual Pico W hardware
- [ ] Verify Wi-Fi connectivity
- [ ] Test motor control
- [ ] Check LCD display
- [ ] Verify watchdog functionality

### For Controller Changes
- [ ] Python syntax check
- [ ] Test with actual Xbox controller
- [ ] Verify network communication
- [ ] Check reconnection logic
- [ ] Test error handling

### For Documentation
- [ ] Spelling and grammar check
- [ ] Verify all links work
- [ ] Test code examples
- [ ] Check formatting (Markdown)

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

All contributors will be acknowledged in the project README and documentation.

## 📞 Questions?

- Open an issue for discussion
- Email: robotics@stclaircollege.ca
- Join our Discord (link in README)

## 🎓 Learning Resources

New to robotics or MicroPython? Check out:
- [MicroPython Documentation](https://docs.micropython.org/)
- [Raspberry Pi Pico W Guide](https://www.raspberrypi.com/documentation/microcontrollers/)
- [pygame Documentation](https://www.pygame.org/docs/)

---

Thank you for helping make this project better! 🤖
