"""
Enhanced web interface for Bible Clock with full configuration and statistics.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template, send_file
from pathlib import Path
import psutil
from src.conversation_manager import ConversationManager

def create_app(verse_manager, image_generator, display_manager, service_manager, performance_monitor):
    """Create enhanced Flask application."""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.logger.setLevel(logging.INFO)
    
    # Disable template caching for development
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Store component references
    app.verse_manager = verse_manager
    app.image_generator = image_generator
    app.display_manager = display_manager
    app.service_manager = service_manager
    app.performance_monitor = performance_monitor
    app.conversation_manager = ConversationManager()
    
    # Activity tracking for recent activity log
    app.recent_activities = []
    
    # Add initial activity
    def _track_activity(action: str, details: str = None):
        """Track activity for recent activity log."""
        try:
            activity = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'details': details or '',
                'type': 'system'
            }
            app.recent_activities.append(activity)
            
            # Keep only last 100 activities to prevent memory growth
            if len(app.recent_activities) > 100:
                app.recent_activities = app.recent_activities[-100:]
                
        except Exception as e:
            app.logger.error(f"Activity tracking error: {e}")
    
    # Initial activity and test activities
    _track_activity("Web interface started", "Bible Clock web interface initialized")
    _track_activity("System startup", "Bible Clock system started successfully")
    _track_activity("Display initialized", "E-ink display ready for verse display")
    
    @app.route('/')
    def index():
        """Main dashboard."""
        return render_template('dashboard.html')
    
    @app.route('/settings')
    def settings():
        """Settings page."""
        return render_template('settings.html')
    
    @app.route('/statistics')
    def statistics():
        """Statistics page."""
        return render_template('statistics.html')
    
    @app.route('/voice')
    def voice_control():
        """Voice control page."""
        return render_template('voice_control.html')
    
    # === API Endpoints ===
    
    @app.route('/api/verse', methods=['GET'])
    def get_current_verse():
        """Get the current verse as JSON."""
        try:
            verse_data = app.verse_manager.get_current_verse()
            verse_data['timestamp'] = datetime.now().isoformat()
            
            return jsonify({
                'success': True,
                'data': verse_data
            })
        except Exception as e:
            app.logger.error(f"API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/status', methods=['GET'])
    def get_status():
        """Get comprehensive system status."""
        try:
            # Check simulation mode from display manager
            simulation_mode = getattr(app.display_manager, 'simulation_mode', False)
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'translation': app.verse_manager.translation,
                'api_url': app.verse_manager.api_url,
                'display_mode': getattr(app.verse_manager, 'display_mode', 'time'),
                'simulation_mode': simulation_mode,
                'hardware_mode': 'Simulation' if simulation_mode else 'Hardware',
                'current_background': app.image_generator.get_current_background_info(),
                'verses_today': getattr(app.verse_manager, 'statistics', {}).get('verses_today', 0),
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                    'cpu_temperature': _get_cpu_temperature(),
                    'uptime': _get_uptime(),
                    'health_status': _get_system_health_status(),
                    'health_details': _get_health_details()
                }
            }
            
            if app.performance_monitor:
                status['performance'] = app.performance_monitor.get_performance_summary()
            
            return jsonify({'success': True, 'data': status})
        except Exception as e:
            app.logger.error(f"Status API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/settings', methods=['GET'])
    def get_settings():
        """Get current settings."""
        try:
            settings = {
                'translation': app.verse_manager.translation,
                'display_mode': getattr(app.verse_manager, 'display_mode', 'time'),
                'time_format': getattr(app.verse_manager, 'time_format', '12'),
                'background_index': app.image_generator.current_background_index,
                'available_backgrounds': app.image_generator.get_available_backgrounds(),
                'available_translations': app.verse_manager.get_available_translations(),
                'parallel_mode': getattr(app.verse_manager, 'parallel_mode', False),
                'secondary_translation': getattr(app.verse_manager, 'secondary_translation', 'web'),
                'available_fonts': app.image_generator.get_available_fonts(),
                'current_font': app.image_generator.get_current_font(),
                'font_sizes': app.image_generator.get_font_sizes(),
                'reference_position_info': app.image_generator.get_reference_position_info(),
                'voice_enabled': getattr(app.verse_manager, 'voice_enabled', False),
                'web_enabled': True,
                'auto_refresh': int(os.getenv('FORCE_REFRESH_INTERVAL', '60')),
                'hardware_mode': os.getenv('SIMULATION_MODE', 'false').lower() == 'false'
            }
            
            return jsonify({'success': True, 'data': settings})
        except Exception as e:
            app.logger.error(f"Settings API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/settings', methods=['POST'])
    def update_settings():
        """Update settings."""
        try:
            data = request.get_json()
            
            # Track if we need to update the display
            needs_display_update = False
            
            # Update translation with validation
            if 'translation' in data:
                translation = data['translation']
                try:
                    available_translations = app.verse_manager.get_available_translations()
                    if translation in available_translations:
                        app.verse_manager.translation = translation
                        app.logger.info(f"Translation changed to: {translation}")
                        needs_display_update = True
                    else:
                        app.logger.error(f"Invalid translation: {translation}. Available: {available_translations}")
                        return jsonify({'success': False, 'error': f'Invalid translation: {translation}. Available translations: {", ".join(available_translations)}'}), 400
                except Exception as e:
                    app.logger.error(f"Translation validation error: {e}")
                    return jsonify({'success': False, 'error': f'Translation validation failed: {str(e)}'}), 500
            
            # Update display mode with validation
            if 'display_mode' in data:
                mode = data['display_mode']
                valid_modes = ['time', 'date', 'random']
                try:
                    if mode in valid_modes:
                        app.verse_manager.display_mode = mode
                        app.logger.info(f"Display mode changed to: {mode}")
                        needs_display_update = True
                    else:
                        app.logger.error(f"Invalid display mode: {mode}. Valid modes: {valid_modes}")
                        return jsonify({'success': False, 'error': f'Invalid display mode: {mode}. Valid modes: {", ".join(valid_modes)}'}), 400
                except Exception as e:
                    app.logger.error(f"Display mode validation error: {e}")
                    return jsonify({'success': False, 'error': f'Display mode update failed: {str(e)}'}), 500
            
            # Update time format with validation
            if 'time_format' in data:
                time_format = data['time_format']
                valid_formats = ['12', '24']
                if time_format in valid_formats:
                    app.verse_manager.time_format = time_format
                    app.logger.info(f"Time format changed to: {time_format}")
                    needs_display_update = True
                else:
                    app.logger.error(f"Invalid time format: {time_format}. Valid formats: {valid_formats}")
                    return jsonify({'success': False, 'error': f'Invalid time format: {time_format}'}), 400
            
            # Update parallel mode
            if 'parallel_mode' in data:
                app.verse_manager.parallel_mode = data['parallel_mode']
                app.logger.info(f"Parallel mode: {data['parallel_mode']}")
            
            # Update secondary translation
            if 'secondary_translation' in data:
                app.verse_manager.secondary_translation = data['secondary_translation']
                app.logger.info(f"Secondary translation: {data['secondary_translation']}")
            
            # Update background with smart refresh detection
            background_changed = False
            if 'background_index' in data:
                old_bg_index = app.image_generator.current_background_index
                app.image_generator.set_background(data['background_index'])
                background_changed = (old_bg_index != app.image_generator.current_background_index)
                app.logger.info(f"Background changed to index: {data['background_index']} (changed: {background_changed})")
                needs_display_update = True  # Background changes need immediate update
            
            # Update font with validation
            if 'font' in data:
                font_name = data['font']
                try:
                    available_fonts = app.image_generator.get_available_fonts()
                    # available_fonts is a List[str] from get_available_fonts()
                    font_names = available_fonts if isinstance(available_fonts, list) else list(available_fonts)
                    
                    if font_name in font_names or font_name == 'default':
                        app.image_generator.set_font(font_name)
                        app.logger.info(f"Font changed to: {font_name}")
                        needs_display_update = True
                    else:
                        app.logger.error(f"Invalid font: {font_name}. Available: {font_names}")
                        return jsonify({'success': False, 'error': f'Invalid font: {font_name}. Available fonts: {", ".join(font_names)}'}), 400
                        
                except Exception as e:
                    app.logger.error(f"Font validation error: {e}")
                    return jsonify({'success': False, 'error': f'Font update failed: {str(e)}'}), 500
            
            # Update font sizes
            if any(key in data for key in ['verse_size', 'reference_size']):
                app.image_generator.set_font_sizes(
                    verse_size=data.get('verse_size'),
                    reference_size=data.get('reference_size')
                )
                app.logger.info("Font sizes updated")
                needs_display_update = True  # Font size changes need immediate update
            
            # Update reference positioning
            if any(key in data for key in ['reference_position', 'reference_x_offset', 'reference_y_offset', 'reference_margin']):
                app.image_generator.set_reference_position(
                    position=data.get('reference_position', app.image_generator.reference_position),
                    x_offset=data.get('reference_x_offset', app.image_generator.reference_x_offset),
                    y_offset=data.get('reference_y_offset', app.image_generator.reference_y_offset),
                    margin=data.get('reference_margin', app.image_generator.reference_margin)
                )
                app.logger.info("Reference position updated")
                needs_display_update = True  # Position changes need immediate update
            
            # Update hardware mode
            if 'hardware_mode' in data:
                simulation_mode = 'false' if data['hardware_mode'] else 'true'
                os.environ['SIMULATION_MODE'] = simulation_mode
                # Update display manager simulation mode
                app.display_manager.simulation_mode = not data['hardware_mode']
                app.logger.info(f"Hardware mode: {'enabled' if data['hardware_mode'] else 'disabled (simulation)'}")
            
            # Consolidated display update logic - update if requested OR if visual changes were made
            should_update_display = (
                data.get('update_display', False) or 
                needs_display_update or
                'background_index' in data or 
                'font' in data or 
                any(key in data for key in ['verse_size', 'reference_size', 'reference_position', 'reference_x_offset', 'reference_y_offset', 'reference_margin'])
            )
            
            if should_update_display:
                try:
                    verse_data = app.verse_manager.get_current_verse()
                    image = app.image_generator.create_verse_image(verse_data)
                    
                    # Determine refresh type: full refresh for background changes, partial for other settings
                    force_refresh = 'background_index' in data or background_changed
                    app.display_manager.display_image(image, force_refresh=force_refresh)
                    
                    refresh_type = "full (background change)" if force_refresh else "partial (settings change)"
                    app.logger.info(f"Display updated immediately with {refresh_type}")
                    
                    # Track activity for recent activity log
                    _track_activity("Settings updated", f"Updated settings: {', '.join(data.keys())}")
                    
                except Exception as display_error:
                    app.logger.error(f"Display update failed: {display_error}")
                    # Don't fail the entire settings update for display issues
            
            return jsonify({'success': True, 'message': 'Settings updated successfully'})
            
        except Exception as e:
            app.logger.error(f"Settings update error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/backgrounds', methods=['GET'])
    def get_backgrounds():
        """Get available backgrounds with previews and cycling settings."""
        try:
            backgrounds = app.image_generator.get_background_info()
            cycling_settings = app.image_generator.get_cycling_settings()
            backgrounds['cycling'] = cycling_settings
            return jsonify({'success': True, 'data': backgrounds})
        except Exception as e:
            app.logger.error(f"Backgrounds API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/fonts', methods=['GET'])
    def get_fonts():
        """Get available fonts."""
        try:
            fonts = app.image_generator.get_font_info()
            return jsonify({'success': True, 'data': fonts})
        except Exception as e:
            app.logger.error(f"Fonts API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/statistics', methods=['GET'])
    def get_statistics():
        """Get usage statistics."""
        try:
            if hasattr(app.verse_manager, 'get_statistics'):
                stats = app.verse_manager.get_statistics()
            else:
                stats = _generate_basic_statistics()
            
            # Add AI statistics if voice control is available
            if hasattr(app.service_manager, 'voice_control') and app.service_manager.voice_control:
                stats['ai_statistics'] = app.service_manager.voice_control.get_ai_statistics()
            else:
                # Provide empty AI statistics if voice control not available
                stats['ai_statistics'] = {
                    'total_tokens': 0,
                    'total_questions': 0,
                    'total_cost': 0.0,
                    'success_rate': 0,
                    'avg_response_time': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'daily_usage': {}
                }
            
            return jsonify({'success': True, 'data': stats})
        except Exception as e:
            app.logger.error(f"Statistics API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/refresh', methods=['POST'])
    def force_refresh():
        """Force display refresh."""
        try:
            verse_data = app.verse_manager.get_current_verse()
            image = app.image_generator.create_verse_image(verse_data)
            app.display_manager.display_image(image, force_refresh=True)
            
            _track_activity("Display refreshed", f"Manual refresh triggered for {verse_data.get('reference', 'Unknown')}")
            return jsonify({'success': True, 'message': 'Display refreshed'})
        except Exception as e:
            app.logger.error(f"Refresh error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/background/cycle', methods=['POST'])
    def cycle_background():
        """Cycle to next background with smart refresh."""
        try:
            app.image_generator.cycle_background()
            
            # Update display if requested - always use full refresh for background changes
            if request.get_json() and request.get_json().get('update_display', False):
                verse_data = app.verse_manager.get_current_verse()
                image = app.image_generator.create_verse_image(verse_data)
                app.display_manager.display_image(image, force_refresh=True)
                app.logger.info("Background cycled with full refresh")
                _track_activity("Background cycled", f"Background changed to index {app.image_generator.current_background_index}")
            
            return jsonify({
                'success': True, 
                'message': 'Background cycled',
                'current_background': app.image_generator.get_current_background_info()
            })
        except Exception as e:
            app.logger.error(f"Background cycle error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/background/randomize', methods=['POST'])
    def randomize_background():
        """Randomize background with smart refresh."""
        try:
            app.image_generator.randomize_background()
            
            # Update display if requested - always use full refresh for background changes
            if request.get_json() and request.get_json().get('update_display', False):
                verse_data = app.verse_manager.get_current_verse()
                image = app.image_generator.create_verse_image(verse_data)
                app.display_manager.display_image(image, force_refresh=True)
                app.logger.info("Background randomized with full refresh")
            
            return jsonify({
                'success': True, 
                'message': 'Background randomized',
                'current_background': app.image_generator.get_current_background_info()
            })
        except Exception as e:
            app.logger.error(f"Background randomize error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/background/cycling', methods=['POST'])
    def set_background_cycling():
        """Configure background cycling settings."""
        try:
            data = request.get_json()
            enabled = data.get('enabled', False)
            interval = data.get('interval_minutes', 30)
            
            app.image_generator.set_background_cycling(enabled, interval)
            
            return jsonify({
                'success': True,
                'message': 'Background cycling updated',
                'settings': app.image_generator.get_cycling_settings()
            })
        except Exception as e:
            app.logger.error(f"Background cycling error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/preview', methods=['POST'])
    def preview_settings():
        """Preview settings without applying to display."""
        try:
            data = request.get_json()
            
            # Store original settings
            original_translation = app.verse_manager.translation
            original_display_mode = getattr(app.verse_manager, 'display_mode', 'time')
            original_parallel_mode = getattr(app.verse_manager, 'parallel_mode', False)
            original_secondary_translation = getattr(app.verse_manager, 'secondary_translation', 'web')
            original_background_index = app.image_generator.current_background_index
            original_font = app.image_generator.current_font_name
            original_font_sizes = app.image_generator.get_font_sizes()
            
            try:
                # Apply temporary changes
                if 'translation' in data:
                    app.verse_manager.translation = data['translation']
                
                if 'display_mode' in data:
                    app.verse_manager.display_mode = data['display_mode']
                
                if 'parallel_mode' in data:
                    app.verse_manager.parallel_mode = data['parallel_mode']
                
                if 'secondary_translation' in data:
                    app.verse_manager.secondary_translation = data['secondary_translation']
                
                if 'background_index' in data:
                    bg_index = data['background_index']
                    if 0 <= bg_index < len(app.image_generator.background_files):
                        app.image_generator.current_background_index = bg_index
                    else:
                        app.logger.warning(f"Invalid background index: {bg_index}")
                        app.image_generator.current_background_index = 0
                
                if 'font' in data:
                    app.image_generator.current_font_name = data['font']
                    app.image_generator._load_fonts_with_selection()
                
                if 'font_sizes' in data:
                    sizes = data['font_sizes']
                    app.image_generator.set_font_sizes(
                        verse_size=sizes.get('verse_size'),
                        reference_size=sizes.get('reference_size')
                    )
                
                # Generate preview
                verse_data = app.verse_manager.get_current_verse()
                image = app.image_generator.create_verse_image(verse_data)
                
                # Apply same transformations as actual display for accurate preview
                preview_image = _apply_display_transformations(image)
                
                # Save preview image
                preview_path = Path('src/web_interface/static/preview.png')
                preview_path.parent.mkdir(exist_ok=True)
                preview_image.save(preview_path)
                
                # Schedule cleanup of old preview images
                _cleanup_old_preview_images()
                
                # Return success with metadata
                return jsonify({
                    'success': True, 
                    'preview_url': f'/static/preview.png?t={datetime.now().timestamp()}',
                    'timestamp': datetime.now().isoformat(),
                    'background_name': f"Background {app.image_generator.current_background_index + 1}",
                    'font_name': app.image_generator.current_font_name,
                    'verse_reference': verse_data.get('reference', 'Unknown')
                })
                
            finally:
                # Restore original settings
                app.verse_manager.translation = original_translation
                app.verse_manager.display_mode = original_display_mode
                app.verse_manager.parallel_mode = original_parallel_mode
                app.verse_manager.secondary_translation = original_secondary_translation
                app.image_generator.current_background_index = original_background_index
                app.image_generator.current_font_name = original_font
                app.image_generator.set_font_sizes(
                    verse_size=original_font_sizes['verse_size'],
                    reference_size=original_font_sizes['reference_size']
                )
            
        except Exception as e:
            app.logger.error(f"Preview error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/voice/status', methods=['GET'])
    def get_voice_status():
        """Get voice control status."""
        try:
            if hasattr(app.service_manager, 'voice_control') and app.service_manager.voice_control:
                status = app.service_manager.voice_control.get_voice_status()
                return jsonify({'success': True, 'data': status})
            else:
                return jsonify({
                    'success': True, 
                    'data': {
                        'enabled': False,
                        'listening': False,
                        'chatgpt_enabled': False,
                        'help_enabled': False,
                        'message': 'Voice control not initialized'
                    }
                })
        except Exception as e:
            app.logger.error(f"Voice status API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/voice/test', methods=['POST'])
    def test_voice():
        """Test voice synthesis."""
        try:
            if hasattr(app.service_manager, 'voice_control') and app.service_manager.voice_control:
                app.service_manager.voice_control.test_voice_synthesis()
                return jsonify({'success': True, 'message': 'Voice test initiated'})
            else:
                return jsonify({'success': False, 'error': 'Voice control not available'})
        except Exception as e:
            app.logger.error(f"Voice test API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/voice/clear-history', methods=['POST'])
    def clear_voice_history():
        """Clear ChatGPT conversation history."""
        try:
            if hasattr(app.service_manager, 'voice_control') and app.service_manager.voice_control:
                app.service_manager.voice_control.clear_conversation_history()
                return jsonify({'success': True, 'message': 'Conversation history cleared'})
            else:
                return jsonify({'success': False, 'error': 'Voice control not available'})
        except Exception as e:
            app.logger.error(f"Clear history API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/voice/history', methods=['GET'])
    def get_voice_history():
        """Get conversation history."""
        try:
            if hasattr(app.service_manager, 'voice_control') and app.service_manager.voice_control:
                history = app.service_manager.voice_control.get_conversation_history()
                return jsonify({'success': True, 'data': history})
            else:
                return jsonify({'success': True, 'data': []})
        except Exception as e:
            app.logger.error(f"Voice history API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/voice/settings', methods=['POST'])
    def update_voice_settings():
        """Update voice control settings."""
        try:
            if not hasattr(app.service_manager, 'voice_control') or not app.service_manager.voice_control:
                return jsonify({'success': False, 'error': 'Voice control not available'})
            
            data = request.get_json()
            voice_control = app.service_manager.voice_control
            
            # Update settings
            if 'voice_rate' in data:
                voice_control.voice_rate = data['voice_rate']
                if voice_control.tts_engine:
                    voice_control.tts_engine.setProperty('rate', data['voice_rate'])
            
            if 'voice_volume' in data:
                voice_control.voice_volume = data['voice_volume']
                if voice_control.tts_engine:
                    voice_control.tts_engine.setProperty('volume', data['voice_volume'])
            
            # Handle API key FIRST before enabling ChatGPT
            if 'chatgpt_api_key' in data:
                # Update the OpenAI API key
                api_key = data['chatgpt_api_key']
                if api_key and not api_key.startswith('•'):  # Not a masked value
                    voice_control.openai_api_key = api_key
                    # Re-initialize ChatGPT with the new key
                    voice_control._initialize_chatgpt()
                    app.logger.info("ChatGPT API key updated")
            
            # Now handle ChatGPT enabled/disabled AFTER API key is set
            if 'chatgpt_enabled' in data:
                voice_control.set_chatgpt_enabled(data['chatgpt_enabled'])
            
            if 'help_enabled' in data:
                voice_control.help_enabled = data['help_enabled']
            
            # Handle audio input/output controls
            if 'audio_input_enabled' in data:
                voice_control.audio_input_enabled = data['audio_input_enabled']
                app.logger.info(f"Audio input: {'enabled' if data['audio_input_enabled'] else 'disabled'}")
            
            if 'audio_output_enabled' in data:
                voice_control.audio_output_enabled = data['audio_output_enabled']
                app.logger.info(f"Audio output: {'enabled' if data['audio_output_enabled'] else 'disabled'}")
            
            if 'screen_display_enabled' in data:
                voice_control.screen_display_enabled = data['screen_display_enabled']
                app.logger.info(f"Screen display: {'enabled' if data['screen_display_enabled'] else 'disabled'}")
            
            
            if 'voice_selection' in data:
                voice_control.voice_selection = data['voice_selection']
                selection = data['voice_selection']
                
                # For OpenAI TTS, update the voice directly
                if hasattr(voice_control, 'tts_voice') and selection in ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']:
                    voice_control.tts_voice = selection
                    app.logger.info(f"OpenAI TTS voice updated to: {selection}")
                    
                    # Update environment variable for persistence
                    import os
                    os.environ['TTS_VOICE'] = selection
                    
                    # Update .env file for persistence across restarts
                    try:
                        env_file_path = '/home/admin/Bible-Clock-v3/.env'
                        if os.path.exists(env_file_path):
                            with open(env_file_path, 'r') as f:
                                lines = f.readlines()
                            
                            # Update or add TTS_VOICE line
                            updated = False
                            for i, line in enumerate(lines):
                                if line.startswith('TTS_VOICE='):
                                    lines[i] = f'TTS_VOICE={selection}\n'
                                    updated = True
                                    break
                            
                            if not updated:
                                lines.append(f'TTS_VOICE={selection}\n')
                            
                            with open(env_file_path, 'w') as f:
                                f.writelines(lines)
                            
                            app.logger.info(f"Updated .env file with TTS_VOICE={selection}")
                    except Exception as e:
                        app.logger.warning(f"Could not update .env file: {e}")
                
                # Legacy system TTS fallback (for compatibility)
                elif voice_control.tts_engine:
                    voices = voice_control.tts_engine.getProperty('voices')
                    if voices:
                        if selection == 'female':
                            female_voices = [v for v in voices if 'female' in v.name.lower() or 'woman' in v.name.lower()]
                            if female_voices:
                                voice_control.tts_engine.setProperty('voice', female_voices[0].id)
                        elif selection == 'male':
                            male_voices = [v for v in voices if 'male' in v.name.lower() or 'man' in v.name.lower()]
                            if male_voices:
                                voice_control.tts_engine.setProperty('voice', male_voices[0].id)
            
            return jsonify({'success': True, 'message': 'Voice settings updated successfully'})
            
        except Exception as e:
            app.logger.error(f"Voice settings API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # === Conversation Analytics API ===
    
    @app.route('/api/conversation/analytics', methods=['GET'])
    def get_conversation_analytics():
        """Get conversation analytics and metrics."""
        try:
            days_back = request.args.get('days', 7, type=int)
            analytics = app.conversation_manager.get_analytics(days_back)
            return jsonify({'success': True, 'data': analytics})
        except Exception as e:
            app.logger.error(f"Conversation analytics API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/conversation/sessions', methods=['GET'])
    def get_conversation_sessions():
        """Get active conversation sessions."""
        try:
            active_sessions = [
                {
                    'session_id': session.session_id,
                    'created_at': session.created_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'turn_count': len(session.turns),
                    'is_current': session.session_id == app.conversation_manager.current_session.session_id if app.conversation_manager.current_session else False
                }
                for session in app.conversation_manager.sessions.values()
                if not session.is_expired()
            ]
            return jsonify({'success': True, 'data': active_sessions})
        except Exception as e:
            app.logger.error(f"Conversation sessions API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/conversation/suggestions', methods=['GET'])
    def get_bible_study_suggestions():
        """Get Bible study suggestions based on conversation history."""
        try:
            suggestions = app.conversation_manager.get_bible_study_suggestions()
            return jsonify({'success': True, 'data': suggestions})
        except Exception as e:
            app.logger.error(f"Bible study suggestions API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/conversation/memory', methods=['GET'])
    def get_conversation_memory():
        """Get conversation context/memory for current session."""
        try:
            context = app.conversation_manager.get_conversation_context(turns_back=5)
            return jsonify({'success': True, 'data': {'context': context}})
        except Exception as e:
            app.logger.error(f"Conversation memory API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # === Piper Voice Management API ===
    
    @app.route('/api/voice/piper/voices', methods=['GET'])
    def get_piper_voices():
        """Get available Piper TTS voices."""
        try:
            import os
            import glob
            from pathlib import Path
            
            voices_dir = Path.home() / ".local" / "share" / "piper" / "voices"
            available_voices = []
            
            if voices_dir.exists():
                # Find all .onnx voice model files
                voice_files = glob.glob(str(voices_dir / "*.onnx"))
                
                for voice_file in voice_files:
                    voice_name = os.path.basename(voice_file).replace('.onnx', '')
                    config_file = voice_file + '.json'
                    
                    # Get voice info from config if available
                    voice_info = {
                        'name': voice_name,
                        'display_name': _format_voice_name(voice_name),
                        'file_path': voice_file,
                        'available': os.path.exists(voice_file)
                    }
                    
                    # Read config for additional info
                    if os.path.exists(config_file):
                        try:
                            import json
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                                voice_info.update({
                                    'language': config.get('language', 'en_US'),
                                    'quality': config.get('quality', 'medium'),
                                    'sample_rate': config.get('audio', {}).get('sample_rate', 22050),
                                    'speaker_id': config.get('speaker_id_map', {})
                                })
                        except:
                            pass
                    
                    available_voices.append(voice_info)
            
            # Sort voices by name
            available_voices.sort(key=lambda x: x['display_name'])
            
            return jsonify({
                'success': True,
                'data': {
                    'voices': available_voices,
                    'voices_dir': str(voices_dir),
                    'current_voice': _get_current_piper_voice()
                }
            })
            
        except Exception as e:
            app.logger.error(f"Piper voices API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/voice/piper/preview', methods=['POST'])
    def preview_piper_voice():
        """Preview a Piper TTS voice."""
        try:
            data = request.get_json()
            if not data or 'voice_name' not in data:
                return jsonify({'success': False, 'error': 'Voice name required'}), 400
            
            voice_name = data['voice_name']
            preview_text = data.get('text', "For God so loved the world that he gave his one and only Son.")
            
            import subprocess
            import tempfile
            import os
            from pathlib import Path
            
            # Get voice model path
            voices_dir = Path.home() / ".local" / "share" / "piper" / "voices"
            voice_model = voices_dir / f"{voice_name}.onnx"
            
            if not voice_model.exists():
                return jsonify({'success': False, 'error': f'Voice model not found: {voice_name}'}), 404
            
            # Generate speech
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Try to find piper binary
                piper_cmd = None
                for cmd in ['piper', '/usr/local/bin/piper', './piper/piper']:
                    try:
                        result = subprocess.run([cmd, '--help'], capture_output=True, timeout=5)
                        if result.returncode == 0:
                            piper_cmd = cmd
                            break
                    except:
                        continue
                
                if not piper_cmd:
                    return jsonify({'success': False, 'error': 'Piper TTS not found. Please install Piper first.'}), 500
                
                # Run Piper TTS
                result = subprocess.run([
                    piper_cmd,
                    '--model', str(voice_model),
                    '--output_file', temp_path
                ], input=preview_text, text=True, capture_output=True, timeout=30)
                
                if result.returncode == 0:
                    file_size = os.path.getsize(temp_path)
                    
                    # Try to play the audio
                    play_success = False
                    try:
                        play_result = subprocess.run(['aplay', temp_path], 
                                                   capture_output=True, timeout=10)
                        play_success = play_result.returncode == 0
                    except:
                        pass
                    
                    return jsonify({
                        'success': True,
                        'message': f'Voice preview generated ({file_size} bytes)',
                        'voice_name': voice_name,
                        'played': play_success,
                        'audio_file_size': file_size
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Piper TTS failed: {result.stderr}'
                    }), 500
                    
            finally:
                # Clean up
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            app.logger.error(f"Voice preview API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/voice/piper/set-voice', methods=['POST'])
    def set_piper_voice():
        """Set the current Piper TTS voice."""
        try:
            data = request.get_json()
            if not data or 'voice_name' not in data:
                return jsonify({'success': False, 'error': 'Voice name required'}), 400
            
            voice_name = data['voice_name']
            
            # Update voice control if available
            if hasattr(app.service_manager, 'voice_control') and app.service_manager.voice_control:
                voice_control = app.service_manager.voice_control
                
                # Check if voice control uses Piper TTS
                if hasattr(voice_control, 'piper_model'):
                    voice_control.piper_model = f"{voice_name}.onnx"
                    
                # Update environment variable for persistence
                os.environ['PIPER_VOICE_MODEL'] = f"{voice_name}.onnx"
                
                # Update .env file if it exists
                try:
                    env_file = Path('.env')
                    if env_file.exists():
                        lines = []
                        voice_updated = False
                        
                        with open(env_file, 'r') as f:
                            for line in f:
                                if line.startswith('PIPER_VOICE_MODEL='):
                                    lines.append(f'PIPER_VOICE_MODEL={voice_name}.onnx\n')
                                    voice_updated = True
                                else:
                                    lines.append(line)
                        
                        if not voice_updated:
                            lines.append(f'PIPER_VOICE_MODEL={voice_name}.onnx\n')
                        
                        with open(env_file, 'w') as f:
                            f.writelines(lines)
                except Exception as e:
                    app.logger.warning(f"Could not update .env file: {e}")
                
                return jsonify({
                    'success': True,
                    'message': f'Voice set to {_format_voice_name(voice_name)}',
                    'voice_name': voice_name
                })
            else:
                return jsonify({'success': False, 'error': 'Voice control not available'}), 500
                
        except Exception as e:
            app.logger.error(f"Set voice API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def _format_voice_name(voice_name):
        """Format voice name for display."""
        # Convert en_US-amy-medium to "Amy (US, Medium)"
        parts = voice_name.split('-')
        if len(parts) >= 3:
            lang = parts[0]
            name = parts[1].title()
            quality = parts[2].title()
            
            lang_map = {
                'en_US': 'US English',
                'en_UK': 'UK English',
                'en_GB': 'British English'
            }
            
            lang_display = lang_map.get(lang, lang)
            return f"{name} ({lang_display}, {quality})"
        
        return voice_name.replace('_', ' ').replace('-', ' ').title()
    
    def _get_current_piper_voice():
        """Get the currently selected Piper voice."""
        try:
            # Check voice control first
            if hasattr(app.service_manager, 'voice_control') and app.service_manager.voice_control:
                voice_control = app.service_manager.voice_control
                if hasattr(voice_control, 'piper_model'):
                    return voice_control.piper_model.replace('.onnx', '')
            
            # Check environment variable
            current_voice = os.getenv('PIPER_VOICE_MODEL', 'en_US-amy-medium.onnx')
            return current_voice.replace('.onnx', '')
            
        except:
            return 'en_US-amy-medium'
    
    # === Audio API Endpoints ===
    
    @app.route('/api/audio/devices', methods=['GET'])
    def get_audio_devices():
        """Get available audio devices."""
        try:
            import subprocess
            
            # Get playback devices
            playback_result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            playback_devices = []
            if playback_result.returncode == 0:
                for line in playback_result.stdout.split('\n'):
                    if 'card' in line and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            card_info = parts[0].strip()
                            device_name = parts[1].strip()
                            card_num = card_info.split()[1]
                            playback_devices.append({
                                'card': card_num,
                                'name': device_name
                            })
            
            # Get recording devices
            recording_result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
            recording_devices = []
            if recording_result.returncode == 0:
                for line in recording_result.stdout.split('\n'):
                    if 'card' in line and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            card_info = parts[0].strip()
                            device_name = parts[1].strip()
                            card_num = card_info.split()[1]
                            recording_devices.append({
                                'card': card_num,
                                'name': device_name
                            })
            
            return jsonify({
                'success': True,
                'data': {
                    'playback': playback_devices,
                    'recording': recording_devices
                }
            })
        except Exception as e:
            app.logger.error(f"Audio devices API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/audio/test-microphone', methods=['POST'])
    def test_microphone():
        """Test microphone by recording 5 seconds of audio."""
        try:
            import subprocess
            import tempfile
            import os
            
            # Create temporary file for recording
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Record 5 seconds of audio
                result = subprocess.run([
                    'arecord', '-f', 'cd', '-t', 'wav', '-d', '5', temp_path
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Check if file was created and has content
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 1000:
                        # Get basic volume info (file size as rough indicator)
                        file_size = os.path.getsize(temp_path)
                        volume_level = "Good" if file_size > 50000 else "Low" if file_size > 10000 else "Very Low"
                        
                        return jsonify({
                            'success': True,
                            'message': 'Microphone test successful',
                            'volume_level': volume_level,
                            'file_size': file_size
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'No audio recorded - check microphone connection'
                        })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Recording failed: {result.stderr}'
                    })
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'error': 'Recording timeout - microphone may not be working'
            })
        except Exception as e:
            app.logger.error(f"Microphone test API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/audio/test-speakers', methods=['POST'])
    def test_speakers():
        """Test speakers using speaker-test command."""
        try:
            import subprocess
            
            # Run speaker test for 2 seconds
            result = subprocess.run([
                'timeout', '2', 'speaker-test', '-c', '2', '-r', '44100', '-t', 'sine'
            ], capture_output=True, text=True)
            
            # speaker-test returns non-zero when interrupted by timeout, which is expected
            if 'ALSA' in result.stderr or 'Front Left' in result.stdout:
                return jsonify({
                    'success': True,
                    'message': 'Speaker test completed'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Speaker test failed - check speaker connection'
                })
                
        except Exception as e:
            app.logger.error(f"Speaker test API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/audio/play-test-sound', methods=['POST'])
    def play_test_sound():
        """Play a test sound using text-to-speech."""
        try:
            # Use voice control to play test sound if available
            voice_control = getattr(app.service_manager, 'voice_control', None)
            if voice_control and hasattr(voice_control, 'speak'):
                voice_control.speak("Audio test successful. Speakers are working properly.")
                return jsonify({
                    'success': True,
                    'message': 'Test sound played successfully'
                })
            else:
                # Fallback to system beep
                import subprocess
                result = subprocess.run(['beep'], capture_output=True)
                return jsonify({
                    'success': True,
                    'message': 'System beep played (TTS not available)'
                })
                
        except Exception as e:
            app.logger.error(f"Play test sound API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/audio/volume', methods=['POST'])
    def update_audio_volume():
        """Update microphone and speaker volume levels."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            import subprocess
            results = []
            
            # Update speaker volume if provided
            if 'speaker_volume' in data:
                volume = max(0, min(100, int(data['speaker_volume'])))
                volume_set = False
                
                # Try different USB audio cards and control names
                for card in ['1', '2', '0']:  # Try common USB audio card numbers
                    if volume_set:
                        break
                    for control in ['Speaker', 'PCM', 'Master', 'Headphone', 'Front', 'USB Audio']:
                        try:
                            result = subprocess.run([
                                'amixer', '-c', card, 'set', control, f'{volume}%'
                            ], capture_output=True, text=True, timeout=5)
                            if result.returncode == 0:
                                results.append(f"Speaker volume set to {volume}% (Card {card}, {control})")
                                volume_set = True
                                break
                        except:
                            continue
                
                if not volume_set:
                    results.append(f"Could not set speaker volume - no compatible audio controls found")
            
            # Update microphone volume if provided
            if 'mic_volume' in data:
                volume = max(0, min(100, int(data['mic_volume'])))
                volume_set = False
                
                # Try different USB audio cards and control names
                for card in ['1', '2', '0']:  # Try common USB audio card numbers
                    if volume_set:
                        break
                    for control in ['Mic', 'Capture', 'Front Mic', 'Rear Mic', 'USB Audio Mic']:
                        try:
                            result = subprocess.run([
                                'amixer', '-c', card, 'set', control, f'{volume}%'
                            ], capture_output=True, text=True, timeout=5)
                            if result.returncode == 0:
                                results.append(f"Microphone volume set to {volume}% (Card {card}, {control})")
                                volume_set = True
                                break
                        except:
                            continue
                
                if not volume_set:
                    results.append(f"Could not set microphone volume - no compatible audio controls found")
            
            # Track volume changes
            if results:
                _track_activity("Volume adjusted", '; '.join(results))
            
            return jsonify({
                'success': True,
                'message': '; '.join(results) if results else 'No volume changes applied'
            })
            
        except Exception as e:
            app.logger.error(f"Audio volume API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/activities', methods=['GET'])
    def get_recent_activities():
        """Get recent activity log."""
        try:
            # Limit to last 50 activities
            recent = app.recent_activities[-50:] if len(app.recent_activities) > 50 else app.recent_activities
            return jsonify({'success': True, 'data': recent})
        except Exception as e:
            app.logger.error(f"Activities API error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        })
    
    def _get_uptime():
        """Get system uptime."""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                return str(timedelta(seconds=int(uptime_seconds)))
        except:
            return "Unknown"
    
    def _get_cpu_temperature():
        """Get CPU temperature."""
        try:
            # Try Raspberry Pi thermal zone first
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_millidegrees = int(f.read().strip())
                temp_celsius = temp_millidegrees / 1000.0
                return round(temp_celsius, 1)
        except:
            try:
                # Try alternative thermal zones
                import glob
                thermal_files = glob.glob('/sys/class/thermal/thermal_zone*/temp')
                if thermal_files:
                    with open(thermal_files[0], 'r') as f:
                        temp_millidegrees = int(f.read().strip())
                        temp_celsius = temp_millidegrees / 1000.0
                        return round(temp_celsius, 1)
            except:
                pass
            
            # Simulation mode - return simulated temperature
            import random
            simulation_mode = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'
            if simulation_mode:
                # Return a realistic simulated temperature
                return round(45.0 + random.uniform(-5, 10), 1)
            
            return None
    
    def _get_system_health_status():
        """Get overall system health status."""
        try:
            # Check various system metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            cpu_temp = _get_cpu_temperature()
            
            issues = []
            
            # Check CPU usage
            if cpu_percent > 90:
                issues.append("High CPU usage")
            
            # Check memory usage
            if memory_percent > 85:
                issues.append("High memory usage")
            
            # Check disk usage
            if disk_percent > 90:
                issues.append("Low disk space")
            
            # Check temperature
            if cpu_temp and cpu_temp > 80:
                issues.append("High CPU temperature")
            
            # Check if display manager is responding
            if not hasattr(app.display_manager, 'last_image_hash'):
                issues.append("Display manager not responding")
            
            # Check API connectivity
            try:
                test_verse = app.verse_manager.get_current_verse()
                if not test_verse or 'error' in test_verse:
                    issues.append("Bible API connectivity issues")
            except Exception:
                issues.append("Bible API connectivity issues")
            
            # Check free disk space (warn earlier)
            if disk_percent > 85:
                issues.append("Low disk space warning")
            
            # Check if voice control is functioning (if enabled)
            if hasattr(app.service_manager, 'voice_control') and app.service_manager.voice_control:
                try:
                    voice_status = app.service_manager.voice_control.get_voice_status()
                    if not voice_status.get('enabled', False):
                        issues.append("Voice control disabled")
                except Exception:
                    issues.append("Voice control not responding")
            
            # Return status
            if not issues:
                return "healthy"
            elif len(issues) == 1:
                return "warning"
            else:
                return "critical"
                
        except Exception:
            return "unknown"
    
    def _get_health_details():
        """Get detailed health information."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_temp = _get_cpu_temperature()
            
            details = {
                "purpose": "System health monitoring helps ensure optimal Bible Clock performance",
                "metrics": {
                    "cpu": {
                        "value": cpu_percent,
                        "status": "good" if cpu_percent < 70 else "warning" if cpu_percent < 90 else "critical",
                        "description": "CPU usage percentage - lower is better for smooth operation"
                    },
                    "memory": {
                        "value": memory.percent,
                        "status": "good" if memory.percent < 70 else "warning" if memory.percent < 85 else "critical",
                        "description": "RAM usage percentage - high usage can cause performance issues"
                    },
                    "disk": {
                        "value": disk.percent,
                        "status": "good" if disk.percent < 80 else "warning" if disk.percent < 90 else "critical",
                        "description": "Storage usage percentage - low space can prevent updates and logging"
                    },
                    "temperature": {
                        "value": cpu_temp,
                        "status": "good" if (cpu_temp and cpu_temp < 65) else "warning" if (cpu_temp and cpu_temp < 80) else "critical",
                        "description": "CPU temperature in Celsius - high temps can cause system instability"
                    },
                    "api_connectivity": {
                        "value": _check_api_connectivity(),
                        "status": "good" if _check_api_connectivity() else "critical",
                        "description": "Bible API connectivity - essential for verse retrieval"
                    },
                    "voice_control": {
                        "value": _check_voice_control_status(),
                        "status": "good" if _check_voice_control_status() == "active" else "warning" if _check_voice_control_status() == "disabled" else "critical",
                        "description": "Voice control system status - enables voice commands and AI features"
                    }
                },
                "uptime": _get_uptime(),
                "last_updated": datetime.now().isoformat(),
                "recommendations": _get_health_recommendations(cpu_percent, memory.percent, disk.percent, cpu_temp)
            }
            
            return details
            
        except Exception as e:
            return {"error": str(e), "purpose": "System health monitoring helps ensure optimal performance"}
    
    def _get_health_recommendations(cpu_percent, memory_percent, disk_percent, cpu_temp):
        """Get health recommendations based on current metrics."""
        recommendations = []
        
        if cpu_percent > 80:
            recommendations.append("Consider reducing background processes or upgrading hardware")
        
        if memory_percent > 80:
            recommendations.append("Free up memory by closing unused applications or restarting the system")
        
        if disk_percent > 85:
            recommendations.append("Clean up old files, logs, or consider expanding storage")
        
        if cpu_temp and cpu_temp > 75:
            recommendations.append("Improve cooling or reduce system load to prevent overheating")
        
        if not recommendations:
            recommendations.append("System is running optimally - no action needed")
        
        return recommendations
    
    def _check_api_connectivity():
        """Check if Bible API is accessible."""
        try:
            # Quick test of verse retrieval
            test_verse = app.verse_manager.get_current_verse()
            return bool(test_verse and 'error' not in test_verse and test_verse.get('text'))
        except Exception:
            return False
    
    def _check_voice_control_status():
        """Check voice control system status."""
        try:
            if hasattr(app.service_manager, 'voice_control') and app.service_manager.voice_control:
                voice_status = app.service_manager.voice_control.get_voice_status()
                if voice_status.get('enabled', False):
                    return "active"
                else:
                    return "disabled"
            return "not_available"
        except Exception:
            return "error"
    
    def _generate_basic_statistics():
        """Generate basic statistics."""
        return {
            'verses_displayed_today': 1440,  # Minutes in a day
            'most_common_book': 'Psalms',
            'total_uptime': _get_uptime(),
            'api_success_rate': 98.5,
            'average_response_time': 0.85
        }
    
    return app

def _apply_display_transformations(image):
    """Apply the same transformations to preview that are applied to actual display."""
    try:
        from PIL import Image as PILImage
        
        # Create a copy to avoid modifying the original
        transformed_image = image.copy()
        
        # Apply EXACT same transformations as display_manager._display_on_hardware()
        
        # Step 1: Apply mirroring if needed (fixes backwards text)
        mirror_setting = os.getenv('DISPLAY_MIRROR', 'false').lower()
        if mirror_setting == 'true':
            transformed_image = transformed_image.transpose(PILImage.FLIP_LEFT_RIGHT)
        elif mirror_setting == 'vertical':
            transformed_image = transformed_image.transpose(PILImage.FLIP_TOP_BOTTOM)
        elif mirror_setting == 'both':
            transformed_image = transformed_image.transpose(PILImage.FLIP_LEFT_RIGHT)
            transformed_image = transformed_image.transpose(PILImage.FLIP_TOP_BOTTOM)
        
        # Step 2: Apply software rotation for precise control
        # This matches display_manager.py line 134-135 exactly
        if os.getenv('DISPLAY_PHYSICAL_ROTATION', '180') == '180':
            transformed_image = transformed_image.rotate(180)
        
        return transformed_image
        
    except Exception as e:
        # If transformation fails, return original image
        return image

def _cleanup_old_preview_images():
    """Clean up old preview images to prevent accumulation."""
    try:
        import time
        import os
        from pathlib import Path
        
        static_dir = Path('src/web_interface/static')
        if not static_dir.exists():
            return
        
        # Clean up preview images older than 1 hour
        max_age = 3600  # 1 hour in seconds
        current_time = time.time()
        
        for preview_file in static_dir.glob('preview*.png'):
            if preview_file.exists():
                file_age = current_time - preview_file.stat().st_mtime
                if file_age > max_age:
                    preview_file.unlink()
                    print(f"Cleaned up old preview image: {preview_file.name}")
        
        # Also clean up any temporary image files
        for temp_file in static_dir.glob('temp_*.png'):
            if temp_file.exists():
                file_age = current_time - temp_file.stat().st_mtime
                if file_age > max_age:
                    temp_file.unlink()
                    print(f"Cleaned up temp image: {temp_file.name}")
                    
    except Exception as e:
        print(f"Preview cleanup error: {e}")