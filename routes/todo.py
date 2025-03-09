from flask import render_template, request, jsonify, session
from models.db import db, TodoList, TodoTask
from auth.authorization import login_required

def init_app(app):
    @app.route('/todo')
    @login_required
    def todo():
        """Render the TODO lists page."""
        return render_template('todo.html')

    @app.route('/api/todo/lists', methods=['GET'])
    @login_required
    def get_todo_lists():
        user_id = session.get('user_id')
        lists = TodoList.query.filter_by(user_id=user_id).order_by(TodoList.order).all()
        return jsonify([list.to_dict() for list in lists])

    @app.route('/api/todo/lists', methods=['POST'])
    @login_required
    def create_todo_list():
        data = request.json
        user_id = session.get('user_id')
        
        try:
            new_list = TodoList(
                name=data['name'],
                description=data.get('description', ''),
                user_id=user_id
            )
            db.session.add(new_list)
            db.session.commit()
            return jsonify({"success": True, "list": new_list.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)})

    @app.route('/api/todo/lists/<int:list_id>', methods=['GET'])
    @login_required
    def get_todo_list(list_id):
        user_id = session.get('user_id')
        todo_list = TodoList.query.filter_by(id=list_id, user_id=user_id).first()
        if not todo_list:
            return jsonify({"success": False, "error": "Lista não encontrada"}), 404
        return jsonify(todo_list.to_dict())

    @app.route('/api/todo/lists/<int:list_id>', methods=['PUT'])
    @login_required
    def update_todo_list(list_id):
        data = request.json
        user_id = session.get('user_id')
        todo_list = TodoList.query.filter_by(id=list_id, user_id=user_id).first()
        
        if not todo_list:
            return jsonify({"success": False, "error": "Lista não encontrada"}), 404

        try:
            todo_list.name = data.get('name', todo_list.name)
            todo_list.description = data.get('description', todo_list.description)
            todo_list.order = data.get('order', todo_list.order)
            db.session.commit()
            return jsonify({"success": True, "list": todo_list.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)})

    @app.route('/api/todo/lists/<int:list_id>', methods=['DELETE'])
    @login_required
    def delete_todo_list(list_id):
        user_id = session.get('user_id')
        todo_list = TodoList.query.filter_by(id=list_id, user_id=user_id).first()
        
        if not todo_list:
            return jsonify({"success": False, "error": "Lista não encontrada"}), 404

        try:
            db.session.delete(todo_list)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)})

    @app.route('/api/todo/tasks', methods=['POST'])
    @login_required
    def create_todo_task():
        data = request.json
        try:
            # Verificar se a lista pertence ao usuário
            list_id = data['list_id']
            user_id = session.get('user_id')
            todo_list = TodoList.query.filter_by(id=list_id, user_id=user_id).first()
            
            if not todo_list:
                return jsonify({"success": False, "error": "Lista não encontrada"}), 404

            new_task = TodoTask(
                title=data['title'],
                description=data.get('description', ''),
                priority=data['priority'],
                list_id=list_id
            )
            db.session.add(new_task)
            db.session.commit()
            return jsonify({"success": True, "task": new_task.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)})

    @app.route('/api/todo/tasks/<int:task_id>', methods=['PUT'])
    @login_required
    def update_task(task_id):
        data = request.json
        try:
            task = TodoTask.query.get_or_404(task_id)
            
            # Verificar se a lista pertence ao usuário
            user_id = session.get('user_id')
            if task.list.user_id != user_id:
                return jsonify({"success": False, "error": "Acesso negado"}), 403

            if 'completed' in data:
                task.completed = data['completed']
            if 'title' in data:
                task.title = data['title']
            if 'description' in data:
                task.description = data['description']
            if 'priority' in data:
                task.priority = data['priority']
            if 'list_id' in data:
                task.list_id = data['list_id']

            db.session.commit()
            return jsonify({"success": True, "task": task.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)})

    @app.route('/api/todo/tasks/<int:task_id>', methods=['DELETE'])
    @login_required
    def delete_task(task_id):
        try:
            task = TodoTask.query.get_or_404(task_id)
            
            # Verificar se a lista pertence ao usuário
            user_id = session.get('user_id')
            if task.list.user_id != user_id:
                return jsonify({"success": False, "error": "Acesso negado"}), 403

            db.session.delete(task)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)})

    @app.route('/api/todo/tasks/<int:task_id>/order', methods=['PUT'])
    @login_required
    def update_task_order(task_id):
        data = request.json
        try:
            task = TodoTask.query.get_or_404(task_id)
            list_id = data.get('list_id')
            new_order = data.get('order')
            
            # Verifica se a lista pertence ao usuário
            todo_list = TodoList.query.get_or_404(list_id)
            if todo_list.user_id != session.get('user_id'):
                return jsonify({"success": False, "error": "Acesso negado"}), 403
            
            task.list_id = list_id
            task.order = new_order
            db.session.commit()
            
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)})
