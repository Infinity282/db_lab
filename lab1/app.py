from flask import Flask, request, jsonify
from db_utils.elastic.elastic_tool import ElasticTool
from utils import has_all_required_fields

app = Flask(__name__)


@app.route('/api/lab1/report', methods=['POST'])
def get_report_by_date_and_term():
    if not request.is_json:
        return jsonify({'error': 'Запрос должен быть в виде JSON'}), 400

    data = request.get_json()
    required_fields = ['material', 'start_date', 'end_date']
    if not has_all_required_fields(data, required_fields):
        jsonify({
            'error': f"Нет необходимых полей: {required_fields}",
            'received': list(data.keys())
        }), 400

    response_body = {
        'search_term': data['material'],
        'period': f"{data['start_date']} - {data['end_date']}",
        'found_lectures': '',
        'worst_attendees': ''
    }

    elastic_tool = ElasticTool()
    materials = elastic_tool.search_materials_by_content(data['material'])

    # Если материалов нет
    if not materials:
        return jsonify(report=response_body, meta={'status': 'success'}), 200

    # Для дебага
    for material in materials:
        print(f"Material ID: {material['material_id']}")
        print(f"Class ID: {material['class_id']}")
        print(f"Content snippet: {material['content'][:100]}...")
        print("-" * 50)

    return jsonify(report=response_body, meta={'status': 'success'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
